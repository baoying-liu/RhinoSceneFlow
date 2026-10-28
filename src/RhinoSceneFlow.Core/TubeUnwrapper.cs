namespace RhinoSceneFlow.Core;

public sealed record TubeUvResult(UvUnwrapResult Mesh,double LengthMeters,double RadiusMeters,double RadiusVariation);

/// <summary>Metric sweep coordinates with a rotation-minimizing frame. The guide
/// supplies direction; closed curves have explicit length/circumference seams.</summary>
public static class TubeUnwrapper
{
    public static TubeUvResult Unwrap(Vec3[] points,int[] triangles,Vec3[] guide,bool closed,double seamDegrees=0,CancellationToken cancel=default)
    {
        if(guide.Length<3||guide.Length>16384||points.Length<3||triangles.Length<3||triangles.Length%3!=0||triangles.Any(i=>i<0||i>=points.Length)||!double.IsFinite(seamDegrees)||points.Concat(guide).Any(p=>!double.IsFinite(p.X)||!double.IsFinite(p.Y)||!double.IsFinite(p.Z)))throw new ArgumentException("管体和中心线数据无效。");
        int n=guide.Length;var tangent=new Vec3[n];var axis=new Vec3[n];var distance=new double[n];
        for(int i=1;i<n;i++)distance[i]=distance[i-1]+(guide[i]-guide[i-1]).Length;
        double length=distance[^1]+(closed?(guide[0]-guide[^1]).Length:0);
        if(length<1e-8||Enumerable.Range(0,closed?n:n-1).Any(i=>(guide[(i+1)%n]-guide[i]).Length<1e-9))throw new ArgumentException("中心线长度不足。");
        for(int i=0;i<n;i++){int lo=closed?(i+n-1)%n:Math.Max(0,i-1),hi=closed?(i+1)%n:Math.Min(n-1,i+1);tangent[i]=(guide[hi]-guide[lo]).Unit;}
        axis[0]=tangent[0].Cross(Math.Abs(tangent[0].Z)<.9?new Vec3(0,0,1):new Vec3(1,0,0)).Unit;
        for(int i=1;i<n;i++)axis[i]=Transport(axis[i-1],tangent[i-1],tangent[i]);
        double closure=0;
        if(closed){var end=Transport(axis[^1],tangent[^1],tangent[0]);closure=Math.Atan2(tangent[0].Dot(end.Cross(axis[0])),end.Dot(axis[0]));}
        for(int i=0;i<n;i++)axis[i]=Rotate(axis[i],tangent[i],closure*distance[i]/length+seamDegrees*Math.PI/180);
        var along=new double[points.Length];var angle=new double[points.Length];var radii=new double[points.Length];
        for(int v=0;v<points.Length;v++)
        {
            if(v%256==0)cancel.ThrowIfCancellationRequested();double best=double.PositiveInfinity,bestT=0;int segment=0;
            for(int i=0;i<(closed?n:n-1);i++)
            {
                var start=guide[i];var e=guide[(i+1)%n]-start;double t=Math.Clamp((points[v]-start).Dot(e)/e.Dot(e),0,1);double d=(points[v]-start-e*t).Dot(points[v]-start-e*t);
                if(d<best){best=d;bestT=t;segment=i;}
            }
            int next=(segment+1)%n;var direction=(tangent[segment]*(1-bestT)+tangent[next]*bestT).Unit;
            var a0=Transport(axis[segment],tangent[segment],direction);var a1=Transport(axis[next],tangent[next],direction);
            double turn=Math.Atan2(direction.Dot(a0.Cross(a1)),a0.Dot(a1));var a=Rotate(a0,direction,turn*bestT);var b=direction.Cross(a).Unit;
            var center=guide[segment]*(1-bestT)+guide[next]*bestT;var delta=points[v]-center;
            radii[v]=Math.Sqrt(Math.Pow(delta.Dot(a),2)+Math.Pow(delta.Dot(b),2));
            double phi=Math.Atan2(delta.Dot(b),delta.Dot(a));if(phi<0)phi+=2*Math.PI;
            along[v]=distance[segment]+bestT*(guide[next]-guide[segment]).Length;angle[v]=phi;
        }
        var sorted=radii.Order().ToArray();double radius=sorted[sorted.Length/2];
        double variation=sorted.Select(r=>Math.Abs(r-radius)/radius).Order().ElementAt((int)(.99*(sorted.Length-1)));
        if(!double.IsFinite(radius)||radius<1e-8||variation>.05)throw new InvalidOperationException("中心线与等径管体不匹配（半径变化超过 5%），请分段或改用 xatlas。");
        double circumference=2*Math.PI*radius;var uv=new List<Uv>();var source=new List<int>();var indices=new int[triangles.Length];var vertices=new Dictionary<(int,double,double),int>();
        for(int i=0;i<triangles.Length;i+=3)
        {
            var ids=new[]{triangles[i],triangles[i+1],triangles[i+2]};var us=ids.Select(v=>along[v]).ToArray();var vs=ids.Select(v=>angle[v]*radius).ToArray();
            if(closed&&us.Max()-us.Min()>length/2)for(int j=0;j<3;j++)if(us[j]<length/2)us[j]+=length;
            if(vs.Max()-vs.Min()>circumference/2)for(int j=0;j<3;j++)if(vs[j]<circumference/2)vs[j]+=circumference;
            for(int j=0;j<3;j++)
            {
                var key=(ids[j],us[j],vs[j]);if(!vertices.TryGetValue(key,out int index)){index=uv.Count;vertices.Add(key,index);source.Add(ids[j]);uv.Add(new(us[j],vs[j]));}indices[i+j]=index;
            }
        }
        var metrics=UvMetrics.Measure(points,source.ToArray(),indices,uv.ToArray());
        return new(new(source.ToArray(),indices,uv.ToArray(),1,metrics.SurfaceArea,metrics.UvArea,metrics.Median,metrics.P95,metrics.Max,0,metrics.Max),length,radius,variation);
    }
    private static Vec3 Transport(Vec3 a,Vec3 from,Vec3 to)
    {
        var cross=from.Cross(to);double sin=cross.Length,cos=Math.Clamp(from.Dot(to),-1,1);
        if(cos<-.99999)throw new ArgumentException("中心线有折返尖点，请平滑后重试。");
        if(sin>1e-12)a=Rotate(a,cross*(1/sin),Math.Atan2(sin,cos));return (a-to*a.Dot(to)).Unit;
    }
    private static Vec3 Rotate(Vec3 p,Vec3 axis,double radians)=>p*Math.Cos(radians)+axis.Cross(p)*Math.Sin(radians)+axis*(axis.Dot(p)*(1-Math.Cos(radians)));
}

public sealed record UvMetricResult(double SurfaceArea,double UvArea,double Median,double P95,double Max);
public static class UvMetrics
{
    public static UvMetricResult Measure(Vec3[] points,int[] source,int[] indices,Uv[] uv)
    {
        double area=0,textureArea=0;var stretches=new List<double>();
        for(int i=0;i<indices.Length;i+=3)
        {
            var p=points[source[indices[i]]];var e=points[source[indices[i+1]]]-p;var f=points[source[indices[i+2]]]-p;
            double x=e.Length,y=e.Dot(f)/x,z=e.Cross(f).Length/x;
            if(x<1e-12||z<1e-12)throw new InvalidDataException("展开网格包含退化面。");
            var a=uv[indices[i]];var b=uv[indices[i+1]];var c=uv[indices[i+2]];
            double j00=(b.U-a.U)/x,j10=(b.V-a.V)/x,j01=(c.U-a.U-j00*y)/z,j11=(c.V-a.V-j10*y)/z;
            double aa=j00*j00+j10*j10,bb=j00*j01+j10*j11,cc=j01*j01+j11*j11,disc=Math.Sqrt((aa-cc)*(aa-cc)+4*bb*bb);
            double high=Math.Sqrt(Math.Max(0,(aa+cc+disc)/2)),low=Math.Sqrt(Math.Max(0,(aa+cc-disc)/2));
            if(low<1e-9)throw new InvalidDataException("展开包含折叠 / 退化 UV，请检查中心线或划分区域。");
            stretches.Add(Math.Max(high,1/low));area+=x*z/2;textureArea+=Math.Abs((b.U-a.U)*(c.V-a.V)-(b.V-a.V)*(c.U-a.U))/2;
        }
        stretches.Sort();return new(area,textureArea,stretches[stretches.Count/2],stretches[(int)((stretches.Count-1)*.95)],stretches[^1]);
    }
}
