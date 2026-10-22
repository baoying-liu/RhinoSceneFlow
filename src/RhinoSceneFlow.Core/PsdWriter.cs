using System.Buffers.Binary;
using System.Text;

namespace RhinoSceneFlow.Core;

/// <summary>Minimal PSD v1 writer: RGB/8, Unicode pixel layers, transparency, raw planar channels.</summary>
public static class PsdWriter
{
    public static int Save(string path, IPsdImage image, CancellationToken cancellation = default, bool overwrite = true, bool allowEmpty = false)
    {
        var layers = image.GetVisibleLayers(cancellation);
        if (layers.Count == 0 && allowEmpty && image.Groups.Count == 1) layers = [new LayerBounds(0,0,0,1,1)];
        if (layers.Count == 0) throw new InvalidOperationException("No visible surface pixels to export.");
        if (layers.Count > 32767) throw new InvalidOperationException("PSD layer count exceeded.");
        string target = Path.GetFullPath(path);
        string directory = Path.GetDirectoryName(target)!;
        if (!Directory.Exists(directory)) throw new DirectoryNotFoundException(directory);
        string temporary = Path.Combine(directory, $".{Path.GetFileName(target)}.{Guid.NewGuid():N}.tmp");
        try
        {
            using (var stream = new FileStream(temporary, FileMode.CreateNew, FileAccess.ReadWrite, FileShare.None))
                Write(stream, image, layers, cancellation);
            cancellation.ThrowIfCancellationRequested();
            File.Move(temporary, target, overwrite);
        }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
        return layers.Count;
    }

    private static void Write(Stream stream, IPsdImage image, IReadOnlyList<LayerBounds> layers, CancellationToken cancellation)
    {
        var w = new BigEndian(stream);
        w.Ascii("8BPS"); w.U16(1); w.Zero(6); w.U16(4);
        w.U32((uint)image.Height); w.U32((uint)image.Width); w.U16(8); w.U16(3);
        w.U32(0); // RGB has no color mode data.
        w.U32(0); // No optional image resources.
        long maskSection = w.BeginLength();
        long layerSection = w.BeginLength();
        w.I16((short)-layers.Count); // Negative count declares merged transparency channel.
        // PSD layer records/channels are stored bottom-to-top; group IDs are top-to-bottom.
        var fileLayers = layers.Reverse().ToArray();
        foreach (var layer in fileLayers)
        {
            w.U32((uint)layer.Top); w.U32((uint)layer.Left); w.U32((uint)layer.Bottom); w.U32((uint)layer.Right);
            w.U16(4);
            foreach (short channel in new short[] { 0, 1, 2, -1 })
            { w.I16(channel); w.U32(checked((uint)((long)layer.Width * layer.Height + 2))); }
            w.Ascii("8BIM"); w.Ascii("norm"); w.Byte(255); w.Byte(0); w.Byte(8); w.Byte(0);
            long extra = w.BeginLength();
            w.U32(0); w.U32(0); // No separate masks or blending ranges.
            string name = image.Groups[layer.Group].Name;
            byte[] fallback = Encoding.ASCII.GetBytes(name[..Math.Min(name.Length, 255)]);
            w.Byte((byte)fallback.Length); stream.Write(fallback);
            w.Zero((4 - ((fallback.Length + 1) % 4)) % 4);
            w.Ascii("8BIM"); w.Ascii("luni");
            byte[] unicode = Encoding.BigEndianUnicode.GetBytes(name);
            w.U32(checked((uint)(4 + unicode.Length)));
            w.U32((uint)name.Length); stream.Write(unicode);
            if (unicode.Length % 2 != 0) w.Byte(0);
            w.EndLength(extra);
        }
        foreach (var layer in fileLayers)
        {
            var color = image.Groups[layer.Group].Color;
            var row = new byte[layer.Width];
            for (int channel = 0; channel < 4; channel++)
            {
                w.U16(0); // Raw compression, no per-row headers.
                if (channel < 3) Array.Fill(row, channel switch { 0 => color.R, 1 => color.G, _ => color.B });
                for (int y = layer.Top; y < layer.Bottom; y++)
                {
                    cancellation.ThrowIfCancellationRequested();
                    if (channel == 3)
                        for (int x = layer.Left; x < layer.Right; x++) row[x - layer.Left] = image.LayerAlpha(layer.Group, x, y);
                    stream.Write(row);
                }
            }
        }
        if ((stream.Position - layerSection - 4) % 2 != 0) w.Byte(0);
        w.EndLength(layerSection);
        w.U32(0); // Global layer mask.
        w.EndLength(maskSection);
        w.U16(0); // Merged RGBA, planar raw.
        var mergedRow = new byte[image.Width];
        for (int channel = 0; channel < 4; channel++)
            for (int y = 0; y < image.Height; y++)
            {
                cancellation.ThrowIfCancellationRequested();
                for (int x = 0; x < image.Width; x++)
                {
                    byte value = image.CompositeChannel(channel, x, y);
                    // PSD merged RGB stores a white matte when merged transparency is present.
                    // Individual pixel layers above use ordinary straight RGB + alpha.
                    byte alpha = image.CompositeChannel(3, x, y);
                    mergedRow[x] = channel == 3 ? value : (byte)Math.Round(value * alpha / 255.0 + 255 - alpha);
                }
                stream.Write(mergedRow);
            }
        if (stream.Length > 2_000_000_000) throw new InvalidOperationException("Export exceeds the 2 GB PSD limit; reduce resolution or color groups.");
    }

    private sealed class BigEndian(Stream stream)
    {
        public void Byte(byte value) => stream.WriteByte(value);
        public void Zero(int count) { for (int i = 0; i < count; i++) Byte(0); }
        public void Ascii(string value) => stream.Write(Encoding.ASCII.GetBytes(value));
        public void U16(ushort value) { Span<byte> b = stackalloc byte[2]; BinaryPrimitives.WriteUInt16BigEndian(b, value); stream.Write(b); }
        public void I16(short value) => U16(unchecked((ushort)value));
        public void U32(uint value) { Span<byte> b = stackalloc byte[4]; BinaryPrimitives.WriteUInt32BigEndian(b, value); stream.Write(b); }
        public long BeginLength() { long start = stream.Position; U32(0); return start; }
        public void EndLength(long start)
        {
            long end = stream.Position;
            stream.Position = start; U32(checked((uint)(end - start - 4))); stream.Position = end;
        }
    }
}
