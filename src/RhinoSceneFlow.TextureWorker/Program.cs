using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using System.Text.Json;
using RhinoSceneFlow.Core;

if(args.Length!=1)throw new ArgumentException("Expected a texture bake request JSON file.");
var request=JsonSerializer.Deserialize<TextureBakeRequest>(File.ReadAllText(args[0]),MaterialLibrary.Json)??throw new InvalidDataException("Missing texture bake request.");
request.Settings.Validate();
if(request.Version!=1||request.Key.Length!=64||request.Key.Any(c=>!Uri.IsHexDigit(c))||!Path.IsPathFullyQualified(request.OutputDirectory)||!request.Maps.ContainsKey("baseColor")||request.Maps.Keys.Any(k=>!MaterialLibrary.Slots.Contains(k)))throw new InvalidDataException("Invalid texture bake request.");
var sampler=new RandomTextureSampler(request.Settings,request.Seed,request.WidthMeters,request.HeightMeters);
string target=Path.GetFullPath(request.OutputDirectory),parent=Path.GetDirectoryName(target)!;Directory.CreateDirectory(parent);
// Cache leases are independent of the short metadata transaction lock.
FileStream? lease=null;var clock=System.Diagnostics.Stopwatch.StartNew();
while(lease==null){try{lease=new FileStream(target+".lock",FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None);}catch(IOException){if(clock.Elapsed.TotalMinutes>10)throw;await Task.Delay(100);}}
using(lease)
{
    if(File.Exists(Path.Combine(target,"manifest.json"))){Console.WriteLine("Cached");return;}
    if(Directory.Exists(target))throw new InvalidDataException("Random texture cache is incomplete; choose a new seed to create a new cache.");
    string staging=Path.Combine(parent,".staging-"+Guid.NewGuid().ToString("N")[..16]);Directory.CreateDirectory(staging);
    try
    {
        var manifest=new TextureBakeManifest{Key=request.Key,WidthMeters=request.WidthMeters*sampler.Span,HeightMeters=request.HeightMeters*sampler.Span};int mapIndex=0;
        foreach(var (slot,path) in request.Maps)
        {
            if(!request.Sha256.TryGetValue(slot,out var hash)||RandomImage.Hash(path)!=hash)throw new InvalidDataException("Source image changed: "+slot);
            using var original=new Bitmap(path);int w=original.Width,h=original.Height;
            if(w>8192/sampler.Span||h>8192/sampler.Span)throw new InvalidDataException("Random texture exceeds 8192 pixels. Reduce the repeat span; source detail is never silently downsampled.");
            using var source=new Bitmap(w,h,PixelFormat.Format32bppArgb);using(var g=Graphics.FromImage(source))g.DrawImageUnscaled(original,0,0);
            var rect=new Rectangle(0,0,w,h);var bits=source.LockBits(rect,ImageLockMode.ReadOnly,PixelFormat.Format32bppArgb);var rgb=new byte[checked(w*h*3)];var row=new byte[w*4];
            try{for(int y=0;y<h;y++){Marshal.Copy(bits.Scan0+y*bits.Stride,row,0,row.Length);for(int x=0;x<w;x++){if(slot=="baseColor"&&row[x*4+3]!=255)throw new InvalidDataException("Randomization currently requires opaque base color.");for(int c=0;c<3;c++)rgb[(y*w+x)*3+c]=row[x*4+2-c];}}}finally{source.UnlockBits(bits);}
            var image=new RandomImage(w,h,rgb);int ow=w*sampler.Span,oh=h*sampler.Span;
            using var output=new Bitmap(ow,oh,PixelFormat.Format24bppRgb);var outputBits=output.LockBits(new Rectangle(0,0,ow,oh),ImageLockMode.WriteOnly,PixelFormat.Format24bppRgb);
            try
            {
                int completedRows=0,checkpoint=Math.Max(1,oh/20);
                Parallel.For(0,oh,new ParallelOptions{MaxDegreeOfParallelism=Math.Min(8,Environment.ProcessorCount)},y=>
                {
                    var scan=new byte[Math.Abs(outputBits.Stride)];
                    for(int x=0;x<ow;x++)
                    {
                        var c=sampler.Sample(image,(x+.5)/w,1-(y+.5)/h,slot);bool color=slot=="baseColor";
                        scan[x*3]=RandomImage.Encode(c.B,color);scan[x*3+1]=RandomImage.Encode(c.G,color);scan[x*3+2]=RandomImage.Encode(c.R,color);
                    }
                    Marshal.Copy(scan,0,outputBits.Scan0+y*outputBits.Stride,scan.Length);
                    int count=Interlocked.Increment(ref completedRows);if(count%checkpoint==0||count==oh)Console.WriteLine($"PROGRESS {mapIndex} {count} {oh} {request.Maps.Count}");
                });
            }
            finally{output.UnlockBits(outputBits);}
            string name=request.Key[..24]+"_"+slot+".png",destination=Path.Combine(staging,name);using(var stream=new FileStream(destination,FileMode.CreateNew,FileAccess.Write,FileShare.None)){output.Save(stream,ImageFormat.Png);stream.Flush(true);}manifest.Maps[slot]=name;manifest.Sha256[slot]=RandomImage.Hash(destination);
            mapIndex++;Console.WriteLine($"MAP {mapIndex}/{request.Maps.Count}");
        }
        using(var file=new FileStream(Path.Combine(staging,"manifest.json"),FileMode.CreateNew,FileAccess.Write,FileShare.None)){byte[] data=System.Text.Encoding.UTF8.GetBytes(JsonSerializer.Serialize(manifest,MaterialLibrary.Json));file.Write(data);file.Flush(true);}
        var publish=System.Diagnostics.Stopwatch.StartNew();
        while(true){try{Directory.Move(staging,target);break;}catch(IOException) when(publish.Elapsed.TotalSeconds<2){await Task.Delay(40);}}
        Console.WriteLine("Completed");
    }
    finally
    {
        // This is the unique staging directory created above, under the explicitly
        // requested cache parent. Never remove a published cache used by Rhino.
        if(!Path.GetFullPath(staging).StartsWith(parent+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase))throw new InvalidDataException("Unexpected cache staging path.");
        if(Directory.Exists(staging))Directory.Delete(staging,true);
    }
}
