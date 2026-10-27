using System.Diagnostics;
using System.Text.Json;

namespace RhinoSceneFlow.Core;

public sealed record UvUnwrapResult(int[] SourceVertices,int[] Indices,Uv[] Coordinates,int Charts,double SurfaceArea,double UvArea,double StretchMedian,double Stretch95,double StretchMax,int RepairedTriangles,double? RawStretchMax);

/// <summary>Native xatlas is isolated in an owned process. Input positions and output UVs are meters.</summary>
public static class XatlasRunner
{
    public static async Task<UvUnwrapResult> RunAsync(string executable,Vec3[] vertices,int[] indices,Action<string,int>? progress=null,CancellationToken cancel=default)
    {
        if(vertices.Length<3||vertices.Length>2_000_000||indices.Length<3||indices.Length%3!=0||indices.Length>18_000_000)throw new ArgumentException("Unsupported unwrap mesh size.");
        if(vertices.Any(p=>!double.IsFinite(p.X)||!double.IsFinite(p.Y)||!double.IsFinite(p.Z))||indices.Any(i=>i<0||i>=vertices.Length))throw new ArgumentException("Invalid unwrap mesh.");
        string directory=Directory.CreateTempSubdirectory("SceneFlow-UV-").FullName;
        using var timeout=CancellationTokenSource.CreateLinkedTokenSource(cancel);timeout.CancelAfter(TimeSpan.FromMinutes(10));var token=timeout.Token;
        try
        {
            string input=Path.Combine(directory,"input.bin"),output=Path.Combine(directory,"output.bin");
            using(var w=new BinaryWriter(File.Create(input))){w.Write(0x31565553u);w.Write(vertices.Length);w.Write(indices.Length);foreach(var p in vertices){w.Write((float)p.X);w.Write((float)p.Y);w.Write((float)p.Z);}foreach(int i in indices)w.Write(i);}
            var info=new ProcessStartInfo(executable){UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true,WorkingDirectory=directory};
            info.ArgumentList.Add(input);info.ArgumentList.Add(output);using var process=new Process{StartInfo=info};
            void Stop(){try{if(!process.HasExited)process.Kill(true);}catch(InvalidOperationException){}catch(System.ComponentModel.Win32Exception){}}
            process.Start();using var stop=token.Register(Stop);
            try
            {
            var stderr=process.StandardError.ReadToEndAsync(token);
            while(await process.StandardOutput.ReadLineAsync(token) is {} line)
            {
                using var parsed=JsonDocument.Parse(line);var e=parsed.RootElement;
                progress?.Invoke(e.GetProperty("stage").GetString()??"xatlas",e.TryGetProperty("percent",out var n)?n.GetInt32():100);
            }
            await process.WaitForExitAsync(token);string error=await stderr;
            if(process.ExitCode!=0)throw new InvalidOperationException("xatlas failed: "+error.Trim());
            token.ThrowIfCancellationRequested();return Read(output,vertices,indices);
            }
            finally{Stop();await process.WaitForExitAsync(CancellationToken.None);}
        }
        catch(OperationCanceledException) when(!cancel.IsCancellationRequested){throw new TimeoutException("xatlas exceeded ten minutes; the owned worker was stopped.");}
        finally{if(Directory.Exists(directory))Directory.Delete(directory,true);}
    }
    private static UvUnwrapResult Read(string path,Vec3[] positions,int[] input)
    {
        using var r=new BinaryReader(File.OpenRead(path));if(r.ReadUInt32()!=0x32565553u)throw new InvalidDataException("Invalid UV result.");
        int nv=r.ReadInt32(),ni=r.ReadInt32(),charts=r.ReadInt32();
        if(nv<3||nv>input.Length||ni!=input.Length||charts<1||r.BaseStream.Length!=16L+24L*nv+4L*ni)throw new InvalidDataException("UV result dimensions are invalid.");
        var source=new int[nv];var uv=new Uv[nv];var chartIds=new List<int>();
        for(int i=0;i<nv;i++){source[i]=r.ReadInt32();int chart=r.ReadInt32();chartIds.Add(chart);uv[i]=new(r.ReadDouble(),r.ReadDouble());if(source[i]<0||source[i]>=positions.Length||chart<0||chart>=charts||!double.IsFinite(uv[i].U)||!double.IsFinite(uv[i].V))throw new InvalidDataException("Invalid UV vertex.");}
        var indices=new int[ni];for(int i=0;i<ni;i++){indices[i]=r.ReadInt32();if(indices[i]<0||indices[i]>=nv||source[indices[i]]!=input[i])throw new InvalidDataException("xatlas changed face correspondence.");}
        double area=0,uvArea=0;
        for(int i=0;i<ni;i+=3){var a=positions[source[indices[i]]];var b=positions[source[indices[i+1]]];var c=positions[source[indices[i+2]]];area+=(b-a).Cross(c-a).Length/2;uvArea+=Area(uv[indices[i]],uv[indices[i+1]],uv[indices[i+2]]);}
        if(area<=0||uvArea<=0)throw new InvalidDataException("Unwrap has zero area.");
        double scale=Math.Sqrt(area/uvArea);for(int i=0;i<nv;i++)uv[i]=new(uv[i].U*scale,uv[i].V*scale);
        double Stretch(int i)
        {
            var e=positions[source[indices[i+1]]]-positions[source[indices[i]]];var f=positions[source[indices[i+2]]]-positions[source[indices[i]]];
            double x=e.Length,y=e.Dot(f)/x,z=Math.Sqrt(Math.Max(0,f.Dot(f)-y*y));if(x<1e-12||z<1e-12)return 1;
            var a=uv[indices[i]];var b=uv[indices[i+1]];var c=uv[indices[i+2]];
            double j00=(b.U-a.U)/x,j10=(b.V-a.V)/x,j01=((c.U-a.U)-j00*y)/z,j11=((c.V-a.V)-j10*y)/z;
            double aa=j00*j00+j10*j10,bb=j00*j01+j10*j11,cc=j01*j01+j11*j11,disc=Math.Sqrt(Math.Max(0,(aa-cc)*(aa-cc)+4*bb*bb));
            double smin=Math.Sqrt(Math.Max(0,(aa+cc-disc)/2)),smax=Math.Sqrt(Math.Max(0,(aa+cc+disc)/2));
            return smin<1e-9?double.PositiveInfinity:Math.Max(smax,1/smin);
        }
        var raw=Enumerable.Range(0,ni/3).Select(f=>Stretch(f*3)).ToArray();double rawMax=raw.Max();var bad=Enumerable.Range(0,raw.Length).Where(f=>raw[f]>2).ToArray();
        // Some solver charts contain nearly collapsed boundary faces. Re-cut only
        // those faces into exact metric triangles; never hide distortion in a statistic.
        if(bad.Length>Math.Max(1,ni/150))throw new InvalidDataException("Too many severely stretched triangles; use a cleaner mesh or smaller unwrap regions.");
        if(bad.Length>0)
        {
            var ss=source.ToList();var uu=uv.ToList();double left=uv.Max(v=>v.U)+.01,bottom=0;
            foreach(int face in bad)
            {
                int i=face*3;var p=positions[source[indices[i]]];var e=positions[source[indices[i+1]]]-p;var f=positions[source[indices[i+2]]]-p;
                double x=e.Length,y=e.Dot(f)/x,z=Math.Sqrt(Math.Max(0,f.Dot(f)-y*y));var coords=new[]{new Uv(left,bottom),new Uv(left+x,bottom),new Uv(left+y,bottom+z)};
                // Negative local x can extend left; reserve enough clearance.
                if(y<0)for(int j=0;j<3;j++)coords[j]=new(coords[j].U-y,coords[j].V);
                for(int j=0;j<3;j++){int old=indices[i+j];indices[i+j]=ss.Count;ss.Add(source[old]);uu.Add(coords[j]);chartIds.Add(charts);}
                charts++;bottom+=z+.01;
            }
            var used=indices.Distinct().Order().ToArray();var renumber=used.Select((v,i)=>(v,i)).ToDictionary(t=>t.v,t=>t.i);
            source=used.Select(v=>ss[v]).ToArray();uv=used.Select(v=>uu[v]).ToArray();charts=used.Select(v=>chartIds[v]).Distinct().Count();for(int i=0;i<ni;i++)indices[i]=renumber[indices[i]];
            double repairedArea=0;for(int i=0;i<ni;i+=3)repairedArea+=Area(uv[indices[i]],uv[indices[i+1]],uv[indices[i+2]]);
            double correction=Math.Sqrt(area/repairedArea);for(int i=0;i<uv.Length;i++)uv[i]=new(uv[i].U*correction,uv[i].V*correction);
        }
        var stretches=Enumerable.Range(0,ni/3).Select(f=>Stretch(f*3)).ToList();if(stretches.Any(v=>!double.IsFinite(v)))throw new InvalidDataException("Unwrap contains a collapsed triangle after repair.");
        stretches.Sort();double Percent(double q)=>stretches[Math.Min(stretches.Count-1,(int)(q*(stretches.Count-1)))];
        double actualArea=0;for(int i=0;i<ni;i+=3)actualArea+=Area(uv[indices[i]],uv[indices[i+1]],uv[indices[i+2]]);
        return new(source,indices,uv,charts,area,actualArea,Percent(.5),Percent(.95),stretches[^1],bad.Length,double.IsFinite(rawMax)?rawMax:null);
    }
    private static double Area(Uv a,Uv b,Uv c)=>Math.Abs((b.U-a.U)*(c.V-a.V)-(b.V-a.V)*(c.U-a.U))/2;
}
