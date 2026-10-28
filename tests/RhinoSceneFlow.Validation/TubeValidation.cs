using RhinoSceneFlow.Core;
using System.Text.Json;

internal static class TubeValidation
{
    internal static void Run(string directory)
    {
        const int n=40,m=48;var points=new Vec3[(n+1)*m];var faces=new List<int>();double radius=.7,length=4;
        for(int i=0;i<=n;i++)for(int j=0;j<m;j++)
        {
            double t=2*Math.PI*j/m;points[i*m+j]=new(radius*Math.Cos(t),radius*Math.Sin(t),length*i/n);
            if(i<n){int a=i*m+j,b=(i+1)*m+j,c=(i+1)*m+(j+1)%m,d=i*m+(j+1)%m;faces.AddRange([a,c,b,a,d,c]);}
        }
        var result=TubeUnwrapper.Unwrap(points,faces.ToArray(),Enumerable.Range(0,41).Select(i=>new Vec3(0,0,length*i/40)).ToArray(),false);
        if(Math.Abs(result.LengthMeters-length)>1e-10||Math.Abs(result.RadiusMeters-radius)>1e-10||result.Mesh.StretchMax>1.002)throw new Exception("Straight tube metric / seam regression.");
        for(int i=0;i<faces.Count;i++)if(result.Mesh.SourceVertices[result.Mesh.Indices[i]]!=faces[i])throw new Exception("Tube changed source face correspondence.");
        foreach(var uv in result.Mesh.Coordinates)if(!double.IsFinite(uv.U)||!double.IsFinite(uv.V))throw new Exception("Nonfinite tube UV.");
        for(int i=0;i<faces.Count;i+=3)
        {
            var t=result.Mesh.Indices.Skip(i).Take(3).Select(v=>result.Mesh.Coordinates[v]).ToArray();
            if(t.Max(v=>v.V)-t.Min(v=>v.V)>.2)throw new Exception("Circumference seam interpolates through the atlas.");
        }
        Vec3 Center(double t)=>new(3*Math.Sin(t)+6*Math.Sin(2*t),3*Math.Cos(t)-6*Math.Cos(2*t),-3*Math.Sin(3*t));
        const int rings=240,sides=48;var knot=new Vec3[rings*sides];var knotFaces=new List<int>();var guide=new Vec3[rings];
        for(int i=0;i<rings;i++)
        {
            double t=2*Math.PI*i/rings;guide[i]=Center(t);var tangent=(Center(t+.0001)-Center(t-.0001)).Unit;var a=tangent.Cross(new(0,0,1)).Unit;var b=tangent.Cross(a).Unit;
            for(int j=0;j<sides;j++){double q=2*Math.PI*j/sides;knot[i*sides+j]=guide[i]+a*(radius*Math.Cos(q))+b*(radius*Math.Sin(q));int aa=i*sides+j,bb=((i+1)%rings)*sides+j,cc=((i+1)%rings)*sides+(j+1)%sides,dd=i*sides+(j+1)%sides;knotFaces.AddRange([aa,cc,bb,aa,dd,cc]);}
        }
        var curved=TubeUnwrapper.Unwrap(knot,knotFaces.ToArray(),guide,true);
        if(curved.Mesh.Charts!=1||curved.RadiusVariation>.05||curved.Mesh.Stretch95>2||Math.Abs(curved.Mesh.UvArea/curved.Mesh.SurfaceArea-1)>.02)throw new Exception("Closed tube continuity / physical metric regression.");
        File.WriteAllText(Path.Combine(directory,"tube.json"),JsonSerializer.Serialize(new{curved.LengthMeters,curved.RadiusMeters,curved.RadiusVariation,curved.Mesh.Charts,curved.Mesh.StretchMedian,curved.Mesh.Stretch95,curved.Mesh.StretchMax,curved.Mesh.SurfaceArea,curved.Mesh.UvArea}));
        using var cancel=new CancellationTokenSource();cancel.Cancel();bool stopped=false;try{TubeUnwrapper.Unwrap(knot,knotFaces.ToArray(),guide,true,cancel:cancel.Token);}catch(OperationCanceledException){stopped=true;}if(!stopped)throw new Exception("Tube cancellation failed.");
        Console.WriteLine("PASS: tube metric dimensions, explicit periodic seams, closed-knot continuity, topology and cancellation.");
    }
}
