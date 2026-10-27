using RhinoSceneFlow.Core;
using System.Text.Json;
using System.Diagnostics;

internal static class UnwrapValidation
{
    internal static async Task Run(string output)
    {
        string worker=Path.GetFullPath("artifacts/native-uv-build/Release/SceneFlow.UvWorker.exe");
        if(!File.Exists(worker))throw new FileNotFoundException("Build the native UV worker before validation.");
        var quad=await XatlasRunner.RunAsync(worker,[new(0,0,0),new(2,0,0),new(2,1,0),new(0,1,0)],[0,1,2,0,2,3]);
        if(Math.Abs(quad.SurfaceArea-2)>1e-6||Math.Abs(quad.UvArea-2)>1e-6||quad.StretchMax>1.001)throw new Exception("Planar metric unwrap failed.");
        const int n=240,m=48;var vertices=new Vec3[n*m];var indices=new List<int>();
        Vec3 Center(double t)=>new(3*Math.Sin(t)+6*Math.Sin(2*t),3*Math.Cos(t)-6*Math.Cos(2*t),-3*Math.Sin(3*t));
        for(int i=0;i<n;i++)
        {
            double t=i*2*Math.PI/n;var c=Center(t);var tangent=(Center(t+.0001)-Center(t-.0001)).Unit;var a=tangent.Cross(new(0,0,1)).Unit;var b=tangent.Cross(a).Unit;
            for(int j=0;j<m;j++){double q=j*2*Math.PI/m;vertices[i*m+j]=c+a*(.7*Math.Cos(q))+b*(.7*Math.Sin(q));int a0=i*m+j,b0=((i+1)%n)*m+j,c0=((i+1)%n)*m+(j+1)%m,d0=i*m+(j+1)%m;indices.AddRange([a0,b0,c0,a0,c0,d0]);}
        }
        var watch=Stopwatch.StartNew();var result=await XatlasRunner.RunAsync(worker,vertices,indices.ToArray());watch.Stop();
        if(result.Charts<2||Math.Abs(result.SurfaceArea/result.UvArea-1)>1e-9||result.Stretch95>2||!double.IsFinite(result.StretchMax))throw new Exception("Complex metric unwrap failed.");
        using var cancel=new CancellationTokenSource();cancel.CancelAfter(100);
        bool cancelled=false;try{await XatlasRunner.RunAsync(worker,vertices,indices.ToArray(),cancel:cancel.Token);}catch(OperationCanceledException){cancelled=true;}
        if(!cancelled)throw new Exception("Native unwrap did not cancel.");
        var report=new{triangles=indices.Count/3,result.Charts,result.SurfaceArea,result.UvArea,result.StretchMedian,result.Stretch95,result.StretchMax,seconds=watch.Elapsed.TotalSeconds,cancelled};
        await File.WriteAllTextAsync(Path.Combine(output,"xatlas.json"),JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true}));Console.WriteLine("PASS: native xatlas planar scale, 23040-triangle trefoil, topology, area, stretch and cancellation.");
        // High-density document mesh with millimeter float storage reproduces
        // boundary outliers absent from the smaller double-precision fixture.
        const int denseN=600,denseM=64;var dense=new Vec3[denseN*denseM];var faces=new List<int>();
        for(int i=0;i<denseN;i++)
        {
            double t=i*2*Math.PI/denseN;var c=Center(t);var tangent=(Center(t+.0001)-Center(t-.0001)).Unit;var a=tangent.Cross(new(0,0,1)).Unit;var b=tangent.Cross(a).Unit;
            for(int j=0;j<denseM;j++)
            {
                double q=j*2*Math.PI/denseM;var p=c+a*(.7*Math.Cos(q))+b*(.7*Math.Sin(q));
                dense[i*denseM+j]=new((float)((100+p.X)*1000)/1000.0-100,(float)((100+p.Y)*1000)/1000.0-100,(float)((5+p.Z)*1000)/1000.0-5);
                int aa=i*denseM+j,bb=((i+1)%denseN)*denseM+j,cc=((i+1)%denseN)*denseM+(j+1)%denseM,dd=i*denseM+(j+1)%denseM;faces.AddRange([aa,bb,cc,aa,cc,dd]);
            }
        }
        var quality=await XatlasRunner.RunAsync(worker,dense,faces.ToArray());
        if(quality.StretchMax>2.01||quality.Stretch95>1.5||Math.Abs(quality.SurfaceArea/quality.UvArea-1)>1e-8)throw new Exception("Dense mesh distortion/metric regression.");
        for(int i=0;i<faces.Count;i++)if(quality.SourceVertices[quality.Indices[i]]!=faces[i])throw new Exception("Repair changed source correspondence.");
        await File.WriteAllTextAsync(Path.Combine(output,"xatlas-dense.json"),JsonSerializer.Serialize(new{quality.Charts,quality.RepairedTriangles,quality.RawStretchMax,quality.StretchMax,quality.Stretch95}));
        Console.WriteLine("PASS: dense float document mesh quality, source correspondence and actual area after local re-cut.");
    }
}
