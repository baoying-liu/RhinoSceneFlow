namespace RhinoSceneFlow.Core;

public sealed record PlantExclusionMesh(LayoutTriangle[] Triangles,bool Closed,bool Footprint=false);
/// <summary>Vertical XY footprints in metres. The immutable tree contains no host geometry.</summary>
public sealed class PlantExclusions
{
    private sealed record Node(double X,double Y,double XX,double YY,int Start,int Count,Node? Left=null,Node? Right=null);
    private readonly LayoutTriangle[] triangles;
    private readonly Lazy<Node?> root;
    private readonly double clearance;
    private readonly double[]? transform;
    private readonly Lazy<GeometryPart[]>? geometry;
    private sealed class GeometryPart
    {
        private readonly g3.DMesh3 mesh=new();private readonly g3.DMeshAABBTree3? tree;private readonly Vec3 origin;private readonly bool closed;
        internal GeometryPart(PlantExclusionMesh part)
        {
            closed=part.Closed;if(part.Triangles.Length==0)return;origin=part.Triangles[0].A;
            foreach(var t in part.Triangles){int a=mesh.AppendVertex(G(t.A-origin)),b=mesh.AppendVertex(G(t.B-origin)),c=mesh.AppendVertex(G(t.C-origin));if((t.B-t.A).Cross(t.C-t.A).Length>1e-12)mesh.AppendTriangle(a,b,c);}
            if(mesh.TriangleCount>0)tree=new(mesh,true);
        }
        private static g3.Vector3d G(Vec3 p)=>new(p.X,p.Y,p.Z);
        internal bool Contains(Vec3 point,double margin)
        {
            if(tree==null)return false;var p=G(point-origin);double distance=double.MaxValue;
            int id=tree.FindNearestTriangle(p,out distance);
            return id>=0&&(distance<=margin*margin+1e-18||(closed&&tree.IsInside(p)));
        }
    }
    private readonly PlantExclusions[]? regions;
    public PlantExclusions(LayoutTriangle[] source,double clearanceMeters,double[]? candidateTransform=null,PlantExclusionMesh[]? geometryParts=null)
    {
        if(!double.IsFinite(clearanceMeters)||clearanceMeters<0||clearanceMeters>1000||source.Length>2_000_000)
            throw new ArgumentException("Invalid exclusion footprint or clearance.");
        if(source.Any(t=>new[]{t.A,t.B,t.C}.Any(p=>!double.IsFinite(p.X)||!double.IsFinite(p.Y)||!double.IsFinite(p.Z))))throw new ArgumentException("Invalid exclusion coordinates.");
        if(candidateTransform!=null&&(candidateTransform.Length!=16||candidateTransform.Any(v=>!double.IsFinite(v))))throw new ArgumentException("Invalid exclusion transform.");
        triangles=(LayoutTriangle[])source.Clone();clearance=clearanceMeters;transform=candidateTransform?.ToArray();
        if(geometryParts!=null){var owned=geometryParts.Select(p=>p with{Triangles=p.Triangles.ToArray()}).ToArray();geometry=new(()=>owned.Where(p=>!p.Footprint).Select(p=>new GeometryPart(p)).ToArray());regions=owned.Where(p=>p.Footprint).Select(p=>new PlantExclusions(p.Triangles,clearanceMeters)).ToArray();}
        root=new(()=>triangles.Length>0&&geometryParts==null?Build(0,triangles.Length):null);
    }
    private Node Build(int start,int count)
    {
        double x=double.PositiveInfinity,y=x,xx=double.NegativeInfinity,yy=xx;
        for(int i=start;i<start+count;i++)foreach(var p in new[]{triangles[i].A,triangles[i].B,triangles[i].C}){x=Math.Min(x,p.X);y=Math.Min(y,p.Y);xx=Math.Max(xx,p.X);yy=Math.Max(yy,p.Y);}
        if(count<=12)return new(x,y,xx,yy,start,count);
        bool horizontal=xx-x>=yy-y;
        double Center(LayoutTriangle t)=>horizontal?t.A.X+t.B.X+t.C.X:t.A.Y+t.B.Y+t.C.Y;
        Array.Sort(triangles,start,count,Comparer<LayoutTriangle>.Create((a,b)=>Center(a).CompareTo(Center(b))));
        int half=count/2;return new(x,y,xx,yy,start,count,Build(start,half),Build(start+half,count-half));
    }
    private static double Cross(Vec3 a,Vec3 b,Vec3 p)=>(b.X-a.X)*(p.Y-a.Y)-(b.Y-a.Y)*(p.X-a.X);
    private static double Distance2(Vec3 a,Vec3 b,Vec3 p)
    {
        double x=b.X-a.X,y=b.Y-a.Y,d=x*x+y*y;
        double u=d==0?0:Math.Clamp(((p.X-a.X)*x+(p.Y-a.Y)*y)/d,0,1);
        return Math.Pow(p.X-a.X-u*x,2)+Math.Pow(p.Y-a.Y-u*y,2);
    }
    public bool Contains(Vec3 point)
    {
        if(transform is {} m)point=new(m[0]*point.X+m[1]*point.Y+m[2]*point.Z+m[3],m[4]*point.X+m[5]*point.Y+m[6]*point.Z+m[7],m[8]*point.X+m[9]*point.Y+m[10]*point.Z+m[11]);
        if(geometry!=null)return geometry.Value.Any(g=>g.Contains(point,clearance))||regions!.Any(r=>r.Contains(point));
        var index=root.Value;if(index==null)return false;
        bool Hit(Node n)
        {
            if(point.X<n.X-clearance||point.Y<n.Y-clearance||point.X>n.XX+clearance||point.Y>n.YY+clearance)return false;
            if(n.Left!=null)return Hit(n.Left)||Hit(n.Right!);
            for(int i=n.Start;i<n.Start+n.Count;i++)
            {
                var t=triangles[i];double a=Cross(t.A,t.B,point),b=Cross(t.B,t.C,point),c=Cross(t.C,t.A,point);
                if(Math.Abs(Cross(t.A,t.B,t.C))>1e-14&&((a>=0&&b>=0&&c>=0)||(a<=0&&b<=0&&c<=0)))return true;
                if(Math.Min(Distance2(t.A,t.B,point),Math.Min(Distance2(t.B,t.C,point),Distance2(t.C,t.A,point)))<=clearance*clearance)return true;
            }
            return false;
        }
        return Hit(index);
    }
}
