using System.IO.Compression;

namespace RhinoSceneFlow.Core;

/// <summary>Only visible layer/tile crops are staged. Each layer owns its RGB, including AA edges.</summary>
public sealed class SparseRgbImage : IPsdImage,IDisposable
{
    public const int TileSize=1024;
    private sealed record Crop(string Path,int Left,int Top,int Width,int Height);
    private readonly string directory;
    private readonly FileStream composite;
    private readonly Dictionary<(int Group,int X,int Y),Crop> crops=[];
    private readonly Dictionary<(int Group,int X,int Y),byte[]> cache=[];
    private readonly Queue<(int Group,int X,int Y)> lru=[];
    private readonly LayerBounds[] bounds;
    private readonly byte[] row;
    private int cachedY=-1;
    public int Width{get;}public int Height{get;}public IReadOnlyList<ColorGroup> Groups{get;}
    public SparseRgbImage(string staging,int width,int height,IReadOnlyList<ColorGroup> groups)
    {
        if(width<1||height<1||width>8192||height>8192||groups.Count<1)throw new ArgumentException("Invalid sparse image dimensions or groups.");
        Width=width;Height=height;Groups=groups;directory=Path.Combine(staging,Guid.NewGuid().ToString("N"));Directory.CreateDirectory(directory);
        composite=new(Path.Combine(directory,"rgba"),FileMode.Create,FileAccess.ReadWrite,FileShare.Read);composite.SetLength((long)width*height*4);row=new byte[width*4];
        bounds=Enumerable.Range(0,groups.Count).Select(g=>new LayerBounds(g,width,height,0,0)).ToArray();
    }
    public void WriteTile(int left,int top,IPsdImage tile,CancellationToken token)
    {
        if(left<0||top<0||left%TileSize!=0||top%TileSize!=0||tile.Width>TileSize||tile.Height>TileSize||left+tile.Width>Width||top+tile.Height>Height||tile.Groups.Count!=Groups.Count)throw new ArgumentException("Invalid sparse tile.");
        var rgba=new byte[tile.Width*4];
        for(int y=0;y<tile.Height;y++)
        {
            token.ThrowIfCancellationRequested();for(int x=0;x<tile.Width;x++)for(int c=0;c<4;c++)rgba[x*4+c]=tile.CompositeChannel(c,x,y);
            composite.Position=((long)(top+y)*Width+left)*4;composite.Write(rgba);
        }
        cachedY=-1;
        foreach(var b in tile.GetVisibleLayers(token))
        {
            token.ThrowIfCancellationRequested();var key=(b.Group,left/TileSize,top/TileSize);string path=Path.Combine(directory,$"{b.Group}-{key.Item2}-{key.Item3}");
            using(var file=File.Create(path))using(var compressed=new DeflateStream(file,CompressionLevel.Fastest))
            {
                var data=new byte[b.Width*4];
                for(int y=b.Top;y<b.Bottom;y++)
                {
                    token.ThrowIfCancellationRequested();for(int x=0;x<b.Width;x++)for(int c=0;c<4;c++)data[x*4+c]=tile.LayerChannel(b.Group,c,b.Left+x,y);
                    compressed.Write(data);
                }
            }
            crops.Add(key,new(path,left+b.Left,top+b.Top,b.Width,b.Height));var old=bounds[b.Group];bounds[b.Group]=new(b.Group,Math.Min(old.Left,left+b.Left),Math.Min(old.Top,top+b.Top),Math.Max(old.Right,left+b.Right),Math.Max(old.Bottom,top+b.Bottom));
        }
    }
    public IReadOnlyList<LayerBounds> GetVisibleLayers(CancellationToken cancellation=default)=>bounds.Where(b=>b.Right>b.Left).ToArray();
    public void ReadLayerRow(int group,int channel,int y,int left,Span<byte> destination)
    {
        destination.Clear();
        for(int tx=left/TileSize;tx<=(left+destination.Length-1)/TileSize;tx++)
        {
            var key=(group,tx,y/TileSize);if(!crops.TryGetValue(key,out var crop)||y<crop.Top||y>=crop.Top+crop.Height)continue;
            int first=Math.Max(left,crop.Left),last=Math.Min(left+destination.Length,crop.Left+crop.Width);if(first>=last)continue;
            if(!cache.TryGetValue(key,out var bytes))
            {
                while(cache.Count>=8)cache.Remove(lru.Dequeue());bytes=new byte[checked(crop.Width*crop.Height*4)];
                using var file=File.OpenRead(crop.Path);using var zipped=new DeflateStream(file,CompressionMode.Decompress);zipped.ReadExactly(bytes);cache.Add(key,bytes);lru.Enqueue(key);
            }
            for(int x=first;x<last;x++)destination[x-left]=bytes[((y-crop.Top)*crop.Width+x-crop.Left)*4+channel];
        }
    }
    public byte LayerChannel(int group,int channel,int x,int y){Span<byte> v=stackalloc byte[1];ReadLayerRow(group,channel,y,x,v);return v[0];}
    public byte LayerAlpha(int group,int x,int y)=>LayerChannel(group,3,x,y);
    public void ReadCompositeRow(int channel,int y,Span<byte> destination)
    {
        if(cachedY!=y){composite.Position=(long)y*Width*4;composite.ReadExactly(row);cachedY=y;}
        for(int x=0;x<destination.Length;x++)destination[x]=row[x*4+channel];
    }
    public byte CompositeChannel(int channel,int x,int y){if(cachedY!=y){composite.Position=(long)y*Width*4;composite.ReadExactly(row);cachedY=y;}return row[x*4+channel];}
    public void Dispose(){composite.Dispose();cache.Clear();if(Directory.Exists(directory))Directory.Delete(directory,true);}
}
