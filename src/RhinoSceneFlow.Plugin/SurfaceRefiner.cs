using Rhino.Geometry;
using Rhino.Geometry.Intersect;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

/// <summary>Trim-aware original-surface queries for uncertain mesh shadow samples.
/// All snapshots are owned copies; this class never edits document geometry.</summary>
internal sealed class SurfaceRefiner(Point3d origin) : IDisposable
{
    private readonly record struct Source(GeometryBase Geometry,BoundingBox Bounds,Sphere? Sphere=null,Plane? Plane=null);
    private readonly List<Source> sources=[];
    private readonly List<ThreadLocal<SurfaceRefiner>> workers=[];
    private int queries;
    public int Queries => queries;

    public void AddBrep(Brep source,Transform transform)
    {
        transform=Transform.Translation(-origin.X,-origin.Y,-origin.Z)*transform;
        var copy=source.DuplicateBrep();
        if(!copy.Transform(transform)){copy.Dispose();throw new InvalidOperationException("Cannot transform shadow surface.");}
        Sphere? sphere=null;Plane? plane=null;
        if(copy.Faces.Count==1)
        {
            var face=copy.Faces[0];
            // A closed one-face spherical Brep covers the whole sphere. Partial or
            // trimmed spheres retain the generic trim-aware intersection path.
            if(copy.IsSolid && face.TryGetSphere(out var s,1e-10))sphere=s;
            else if(face.TryGetPlane(out var p,1e-10))plane=p;
        }
        sources.Add(new(copy,sphere?.BoundingBox??copy.GetBoundingBox(true),sphere,plane));
    }

    public void AddMesh(Mesh source,Transform transform)
    {
        transform=Transform.Translation(-origin.X,-origin.Y,-origin.Z)*transform;
        var copy=new Mesh();copy.Vertices.UseDoublePrecisionVertices=true;
        for(int i=0;i<source.Vertices.Count;i++)
        {
            var p=source.Vertices.Point3dAt(i);p.Transform(transform);copy.Vertices.Add(p);
        }
        if(source.Normals.Count==source.Vertices.Count && transform.TryGetInverse(out var inverse))
            foreach(var n in source.Normals)
            {
                var normal=new Vector3d(inverse.M00*n.X+inverse.M10*n.Y+inverse.M20*n.Z,
                    inverse.M01*n.X+inverse.M11*n.Y+inverse.M21*n.Z,inverse.M02*n.X+inverse.M12*n.Y+inverse.M22*n.Z);
                normal.Unitize();copy.Normals.Add(normal);
            }
        foreach(var f in source.Faces)
        {
            copy.Faces.AddFace(f.A,f.B,f.C);
            if(f.IsQuad)copy.Faces.AddFace(f.A,f.C,f.D);
        }
        copy.FaceNormals.ComputeFaceNormals();
        sources.Add(new(copy,copy.GetBoundingBox(true)));
    }

    public Func<int,int,bool> Evaluator(CameraProjection camera,int width,int height,ShadowSettings settings)
    {
        camera=camera with { Origin=camera.Origin-new Vec3(origin.X,origin.Y,origin.Z) };
        var bounds=BoundingBox.Empty;foreach(var s in sources)bounds.Union(s.Bounds);
        double span=Math.Max(bounds.Diagonal.Length,settings.Bias*100);
        // Do not reuse the document modeling tolerance as an occlusion gap.
        double tolerance=Math.Max(1e-10,Math.Min(settings.Bias*.001,span*1e-10));
        var sun=new Vector3d(settings.ToSun.Unit.X,settings.ToSun.Unit.Y,settings.ToSun.Unit.Z);
        // Rhino intersection caches are never shared between worker threads. Each
        // worker owns a deep copy of the already detached, transformed snapshots.
        var local=new ThreadLocal<SurfaceRefiner>(()=>
        {
            var worker=new SurfaceRefiner(origin);
            foreach(var source in sources)
            {
                GeometryBase copy=source.Geometry is Brep b?b.DuplicateBrep():((Mesh)source.Geometry).DuplicateMesh();
                worker.sources.Add(source with { Geometry=copy });
            }
            return worker;
        },trackAllValues:true);
        workers.Add(local);
        return (x,y) =>
        {
            Interlocked.Increment(ref queries);var worker=local.Value!;
            var near=Point(camera.At((x+.5)/(width*2),1-(y+.5)/(height*2),camera.Near));
            var far=Point(camera.At((x+.5)/(width*2),1-(y+.5)/(height*2),camera.Far));
            var view=far-near;double length=view.Length;view.Unitize();
            var hit=worker.Trace(near,view,length,tolerance);
            if(hit is null)return false;
            var n=hit.Value.Normal;var formNormal=hit.Value.FormNormal;
            if(formNormal*n<0)formNormal=-formNormal;
            if(n*view>0){n=-n;formNormal=-formNormal;}
            if(settings.IncludeFormShading && formNormal*sun<=1e-10)return true;
            if(n*sun<=1e-10)return false;
            // The origin moves only along the light ray by the explicit numeric bias;
            // it is never displaced along a smooth normal or mesh-error envelope.
            return worker.Trace(hit.Value.Point+sun*settings.Bias,sun,span*2,tolerance) is not null;
        };
    }

    private readonly record struct Hit(Point3d Point,Vector3d Normal,Vector3d FormNormal,double Distance);

    private Hit? Trace(Point3d origin,Vector3d direction,double maximum,double tolerance)
    {
        Hit? best=null;
        using var line=new LineCurve(origin,origin+direction*maximum);
        foreach(var source in sources)
        {
            var geometry=source.Geometry;var bounds=source.Bounds;
            double limit=best?.Distance ?? maximum;
            if(!Crosses(bounds,origin,direction,limit,tolerance))continue;
            if(source.Sphere is {} sphere)
            {
                var q=origin-sphere.Center;double b=q*direction,c=q*q-sphere.Radius*sphere.Radius;
                double discriminant=b*b-c;
                if(discriminant<0)continue;
                double root=Math.Sqrt(discriminant),distance=-b-root;
                if(distance<0)distance=-b+root;
                if(distance<0||distance>limit)continue;
                var point=origin+direction*distance;var normal=(point-sphere.Center)/sphere.Radius;
                best=new(point,normal,normal,distance);
            }
            else if(source.Plane is {} plane && geometry is Brep planar)
            {
                double slope=plane.Normal*direction;if(Math.Abs(slope)<1e-14)continue;
                double distance=((plane.Origin-origin)*plane.Normal)/slope;
                if(distance<0||distance>limit)continue;
                var point=origin+direction*distance;var face=planar.Faces[0];
                if(!face.ClosestPoint(point,out double u,out double v)||face.IsPointOnFace(u,v,tolerance)==PointFaceRelation.Exterior)continue;
                best=new(point,plane.Normal,plane.Normal,distance);
            }
            else if(geometry is Mesh mesh)
            {
                double distance=Intersection.MeshRay(mesh,new Ray3d(origin,direction),out var faces);
                if(distance<0 || distance>limit || faces.Length==0)continue;
                var fn=mesh.FaceNormals[faces[0]];
                var point=origin+direction*distance;var normal=new Vector3d(fn.X,fn.Y,fn.Z);var formNormal=normal;
                if(mesh.Normals.Count==mesh.Vertices.Count)
                {
                    var mp=mesh.ClosestMeshPoint(point,0);if(mp is not null)formNormal=mesh.NormalAt(mp);
                }
                best=new(point,normal,formNormal,distance);
            }
            else if(geometry is Brep brep)
            {
                Intersection.CurveBrep(line,brep,tolerance,1e-9,out double[] parameters);
                foreach(double parameter in parameters ?? [])
                {
                    var point=line.PointAt(parameter);
                    // CurveBrep supplies a root estimate. Refine it on the original
                    // trimmed face; near a tangent the estimate can otherwise become
                    // a false hit on the very surface where the light ray starts.
                    BrepFace? face=null;double u=0,v=0,error=double.PositiveInfinity;
                    foreach(var candidate in brep.Faces)
                    {
                        if(!candidate.ClosestPoint(point,out double cu,out double cv))continue;
                        if(candidate.IsPointOnFace(cu,cv,tolerance)==PointFaceRelation.Exterior)continue;
                        double e=candidate.PointAt(cu,cv).DistanceTo(point);
                        if(e<error){error=e;face=candidate;u=cu;v=cv;}
                    }
                    if(face is null)continue;
                    double distance=(point-origin)*direction;
                    bool converged=false;
                    Vector3d normal=Vector3d.Unset;
                    for(int step=0;step<12;step++)
                    {
                        point=origin+direction*distance;
                        if(!face.ClosestPoint(point,out u,out v))break;
                        normal=face.NormalAt(u,v);normal.Unitize();
                        double residual=(point-face.PointAt(u,v))*normal;
                        double slope=normal*direction;
                        if(Math.Abs(slope)<1e-12)break;
                        // Bound uncertainty along the ray, not just perpendicular to
                        // the face. A grazing ray can be within surface tolerance at
                        // its origin while its actual root is behind the origin.
                        if(Math.Abs(residual)<=tolerance*Math.Abs(slope)){converged=true;break;}
                        distance-=residual/slope;
                    }
                    if(!converged || distance<0 || distance>limit ||
                        face.IsPointOnFace(u,v,tolerance)==PointFaceRelation.Exterior)continue;
                    // A plane residual alone is insufficient at a trim boundary or
                    // near a degenerate parameterization: check the 3D surface too.
                    if(point.DistanceTo(face.PointAt(u,v))>tolerance*8)continue;
                    best=new(point,normal,normal,distance);limit=distance;
                }
            }
        }
        return best;
    }

    private static bool Crosses(BoundingBox box,Point3d origin,Vector3d direction,double max,double epsilon)
    {
        double enter=0,exit=max;
        for(int axis=0;axis<3;axis++)
        {
            double d=direction[axis],o=origin[axis],low=box.Min[axis]-epsilon,high=box.Max[axis]+epsilon;
            if(Math.Abs(d)<1e-15){if(o<low||o>high)return false;continue;}
            double a=(low-o)/d,b=(high-o)/d;if(a>b)(a,b)=(b,a);
            enter=Math.Max(enter,a);exit=Math.Min(exit,b);if(enter>exit)return false;
        }
        return true;
    }
    private static Point3d Point(Vec3 v)=>new(v.X,v.Y,v.Z);
    public void Dispose()
    {
        foreach(var local in workers){foreach(var worker in local.Values)worker.Dispose();local.Dispose();}workers.Clear();
        foreach(var s in sources)s.Geometry.Dispose();sources.Clear();
    }
}
