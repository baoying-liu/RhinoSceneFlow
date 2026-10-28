using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Render;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class UnwrapJob
{
    public Guid Id{get;}=Guid.NewGuid();
    public string Status{get;internal set;}="running";
    public string Stage{get;internal set;}="正在准备网格";
    public int Percent{get;internal set;}
    public double Seconds{get;internal set;}
    public string? Error{get;internal set;}
    public object[] Results{get;internal set;}=[];
}

public static class UnwrapService
{
    private sealed record Input(Guid Id,uint Crc,string MappingState,string Backup,Point3d Origin,double Scale,Vec3[] Points,Vec3[] Normals,int[] Indices,bool OrientationCorrected);
    private static readonly Dictionary<Guid,(UnwrapJob Job,CancellationTokenSource Cancel)> jobs=[];
    private static bool stopping;
    public static UnwrapJob Get(Guid id)=>jobs.TryGetValue(id,out var value)?value.Job:throw new ArgumentException("展开任务不存在。");
    public static object Cancel(Guid id){if(jobs.TryGetValue(id,out var value)&&value.Job.Status=="running"){value.Cancel.Cancel();value.Job.Stage="正在取消 xatlas";}return Get(id);}
    internal static void StopAll(){stopping=true;foreach(var value in jobs.Values.Where(v=>v.Job.Status=="running"))value.Cancel.Cancel();}
    private static void Ui(Action action){if(!stopping)RhinoApp.InvokeOnUiThread(new Action(()=>{if(!stopping)action();}));}
    public static UnwrapJob Start(RhinoDoc doc,Guid[]? objects,Guid[]? layers,string method="xatlas",Guid? guideId=null)
    {
        if(stopping)throw new InvalidOperationException("Rhino 正在关闭。");
        if(method is not ("xatlas" or "tube"))throw new ArgumentException("展开方式必须为 xatlas 或 tube。");
        Vec3[] guide=[];uint guideCrc=0;bool guideClosed=false;
        if(method=="tube")
        {
            var curve=guideId.HasValue?doc.Objects.FindId(guideId.Value)?.Geometry as Curve:null;
            if(curve==null||!curve.IsValid||curve.GetLength()<doc.ModelAbsoluteTolerance)throw new ArgumentException("管状展开需要有效的中心线 guideId。");
            guideCrc=curve.DataCRC(0);guideClosed=curve.IsClosed;double unit=MaterialService.UnitScale(doc);
            Point3d[] path=curve.TryGetPolyline(out var line)?line.ToArray():(curve.DivideByCount(1200,true)??throw new ArgumentException("中心线采样失败。")).Select(curve.PointAt).ToArray();
            if(path.Length>1&&path[0].DistanceTo(path[^1])<1e-8)path=path[..^1];
            guide=path.Select(p=>new Vec3(p.X/unit,p.Y/unit,p.Z/unit)).ToArray();
        }
        if(jobs.Values.Any(v=>v.Job.Status=="running"))throw new InvalidOperationException("已有 xatlas 任务正在运行。");
        string executable=Path.Combine(Path.GetDirectoryName(typeof(UnwrapService).Assembly.Location)!,"SceneFlow.UvWorker.exe");
        if(!File.Exists(executable))throw new FileNotFoundException("请安装包含 C++ xatlas worker 的完整插件包。",executable);
        double scale=MaterialService.UnitScale(doc);var ids=MaterialService.ResolveTargets(doc,objects,layers);uint serial=doc.RuntimeSerialNumber;
        var clock=System.Diagnostics.Stopwatch.StartNew();var inputs=ids.Select(id=>Capture(doc.Objects.FindId(id)!,scale)).ToArray();var job=new UnwrapJob();var cancel=new CancellationTokenSource();jobs.Add(job.Id,(job,cancel));
        _=Task.Run(async()=>
        {
            try
            {
                var results=new List<UvUnwrapResult>();var tubes=new List<TubeUvResult?>();
                for(int i=0;i<inputs.Length;i++)
                {
                    int item=i;var input=inputs[i];
                    if(method=="tube")
                    {
                        Ui(()=>job.Stage=$"管状连续展开 {item+1}/{inputs.Length}");
                        var origin=new Vec3(input.Origin.X/input.Scale,input.Origin.Y/input.Scale,input.Origin.Z/input.Scale);
                        var tube=TubeUnwrapper.Unwrap(input.Points,input.Indices,guide.Select(p=>p-origin).ToArray(),guideClosed,cancel:cancel.Token);results.Add(tube.Mesh);tubes.Add(tube);
                    }
                    else {tubes.Add(null);results.Add(await XatlasRunner.RunAsync(executable,input.Points,input.Indices,(stage,n)=>Ui(()=>{job.Stage=$"xatlas {item+1}/{inputs.Length} · {stage}";job.Percent=(item*100+n)/inputs.Length;}),cancel.Token));}
                }
                Ui(()=>
                {
                    try
                    {
                        cancel.Token.ThrowIfCancellationRequested();var current=RhinoDoc.FromRuntimeSerialNumber(serial)??throw new InvalidOperationException("原文档已关闭。");
                        if(method=="tube"&&current.Objects.FindId(guideId!.Value)?.Geometry.DataCRC(0)!=guideCrc)throw new InvalidOperationException("中心线在计算期间改变，未应用结果。");
                        foreach(var input in inputs)
                        {
                            var obj=current.Objects.FindId(input.Id)??throw new InvalidOperationException("原物件已删除。");
                            if(obj.Geometry.DataCRC(0)!=input.Crc||MaterialService.UnitScale(current)!=input.Scale||MaterialService.UnwrapMappingState(obj)!=input.MappingState)throw new InvalidOperationException("计算期间物件、单位或 UV 已改变，结果未应用，请重新展开。");
                        }
                        var previous=inputs.Select(input=>
                        {
                            var o=current.Objects.FindId(input.Id)!;
                            var maps=o.GetTextureChannels().Select(ch=>{var map=o.GetTextureMapping(ch,out var x);return (Channel:ch,Map:map,Transform:x);}).ToArray();
                            return (Id:input.Id,Attributes:o.Attributes.Duplicate(),Maps:maps);
                        }).ToArray();
                        uint undo=current.BeginUndoRecord("SceneFlow xatlas 真实尺度展开");int touched=0;
                        try
                        {
                            for(int i=0;i<inputs.Length;i++)
                            {
                                var input=inputs[i];var result=results[i];using var mesh=new Mesh();
                                for(int v=0;v<result.SourceVertices.Length;v++)
                                {
                                    int source=result.SourceVertices[v];var p=input.Points[source];mesh.Vertices.Add(input.Origin+new Vector3d(p.X,p.Y,p.Z)*input.Scale);
                                    var normal=input.Normals[source];mesh.Normals.Add((float)normal.X,(float)normal.Y,(float)normal.Z);
                                    var uv=result.Coordinates[v];mesh.TextureCoordinates.Add((float)uv.U,(float)uv.V);
                                }
                                for(int f=0;f<result.Indices.Length;f+=3)mesh.Faces.AddFace(result.Indices[f],result.Indices[f+1],result.Indices[f+2]);
                                touched=i+1;MaterialService.CommitUnwrapped(current,current.Objects.FindId(input.Id)!,mesh,input.Backup,method,input.OrientationCorrected);
                            }
                        }
                        catch
                        {
                            foreach(var p in previous.Take(touched))
                            {
                                var o=current.Objects.FindId(p.Id)!;
                                foreach(int ch in o.GetTextureChannels().Except(p.Maps.Select(m=>m.Channel)))o.SetTextureMapping(ch,null);
                                foreach(var m in p.Maps)o.SetTextureMapping(m.Channel,m.Map,m.Transform);
                                current.Objects.ModifyAttributes(p.Id,p.Attributes,true);UvRenderProvider.Refresh(current,current.Objects.FindId(p.Id)!);
                            }
                            throw;
                        }
                        finally{foreach(var p in previous){foreach(var m in p.Maps)m.Map?.Dispose();p.Attributes.Dispose();}if(undo!=0)current.EndUndoRecord(undo);}
                        job.Results=inputs.Select((input,i)=>(object)new{input.Id,method,lengthMeters=tubes[i]?.LengthMeters,radiusMeters=tubes[i]?.RadiusMeters,radiusVariation=tubes[i]?.RadiusVariation,orientationCorrected=input.OrientationCorrected,triangles=inputs[i].Indices.Length/3,vertices=results[i].SourceVertices.Length,charts=results[i].Charts,surfaceAreaMeters2=results[i].SurfaceArea,uvAreaMeters2=results[i].UvArea,stretchMedian=results[i].StretchMedian,stretch95=results[i].Stretch95,stretchMax=results[i].StretchMax,repairedTriangles=results[i].RepairedTriangles,rawStretchMax=results[i].RawStretchMax}).ToArray();
                        job.Seconds=clock.Elapsed.TotalSeconds;job.Status="completed";job.Percent=100;job.Stage=method=="tube"?"管状展开完成 · 中心线弧长 / 周长按米计算":"展开完成 · 1 UV 单位 = 1 米（面积校准）";current.Views.Redraw();
                    }
                    catch(OperationCanceledException){job.Status="cancelled";job.Stage="已取消，未应用计算结果";}
                    catch(Exception ex){job.Status="failed";job.Error=ex.Message;job.Stage=ex.Message;}
                });
            }
            catch(OperationCanceledException){Ui(()=>{job.Status="cancelled";job.Stage="已取消，未修改原物件";});}
            catch(Exception ex){Ui(()=>{job.Status="failed";job.Error=ex.Message;job.Stage=ex.Message;});}
        });
        return job;
    }
    private static Input Capture(RhinoObject obj,double scale)
    {
        using var mesh=new Mesh();
        switch(obj.Geometry)
        {
            case Mesh m:mesh.Append(m);break;
            case Brep b:AddBrep(b);break;
            case Extrusion e:using(var b=e.ToBrep())AddBrep(b);break;
            case Surface s:using(var b=s.ToBrep())AddBrep(b);break;
            case SubD sub:using(var m=Mesh.CreateFromSubD(sub,3))mesh.Append(m);break;
            default:throw new NotSupportedException("xatlas 支持网格、Brep、曲面和 SubD；不直接展开块实例。");
        }
        void AddBrep(Brep b){using var p=MeshingParameters.QualityRenderMesh;p.GridMinCount=64;p.RefineGrid=true;foreach(var part in Mesh.CreateFromBrep(b,p)??[]){using(part)mesh.Append(part);}}
        if(mesh.Normals.Count!=mesh.Vertices.Count)mesh.Normals.ComputeNormals();
        mesh.Vertices.CombineIdentical(false,true);mesh.Faces.ConvertQuadsToTriangles();mesh.Faces.CullDegenerateFaces();mesh.Vertices.CullUnused();
        if(mesh.UnifyNormals()>0)mesh.Normals.ComputeNormals();
        bool corrected=false;
        if(mesh.IsClosed&&mesh.DisjointMeshCount==1)
        {
            using var mass=VolumeMassProperties.Compute(mesh);
            if(mass!=null&&mass.Volume<0)
            {
                for(int i=0;i<mesh.Faces.Count;i++){var f=mesh.Faces[i];mesh.Faces.SetFace(i,f.C,f.B,f.A);}
                for(int i=0;i<mesh.Normals.Count;i++)mesh.Normals[i]=-mesh.Normals[i];
                corrected=true;
            }
        }
        var origin=mesh.GetBoundingBox(true).Center;var points=mesh.Vertices.Select(v=>new Vec3((v.X-origin.X)/scale,(v.Y-origin.Y)/scale,(v.Z-origin.Z)/scale)).ToArray();
        var normals=mesh.Normals.Select(n=>new Vec3(n.X,n.Y,n.Z)).ToArray();var indices=mesh.Faces.SelectMany(f=>new[]{f.A,f.B,f.C}).ToArray();
        return new(obj.Id,obj.Geometry.DataCRC(0),MaterialService.UnwrapMappingState(obj),MaterialService.UnwrapBackup(obj),origin,scale,points,normals,indices,corrected);
    }
}

public static partial class MaterialService
{
    internal static string UnwrapBackup(RhinoObject obj)=>Backup(obj);
    internal static string UnwrapMappingState(RhinoObject obj)
    {
        using var m=obj.GetTextureMapping(1,out var x);string hash=m==null?"none":MapHash(m,x);
        if(ReadUv(obj) is {MeshChannel:>1} r){using var stored=obj.GetTextureMapping(r.MeshChannel,out var sx);hash+="/"+(stored==null?"none":MapHash(stored,sx));}return hash;
    }
    internal static void CommitUnwrapped(RhinoDoc doc,RhinoObject obj,Mesh mesh,string backup,string method,bool corrected)
    {
        var old=ReadUv(obj);int channel=1000;bool reuse=false;
        if(old is {Version:2,MeshChannel:>1}){using var previous=obj.GetTextureMapping(old.MeshChannel,out var px);reuse=previous!=null&&MapHash(previous,px)==old.MeshHash;if(reuse)channel=old.MeshChannel;}
        if(!reuse){var used=obj.GetTextureChannels().ToHashSet();while(used.Contains(channel))channel++;}
        using var storage=TextureMapping.CreateCustomMeshMapping(mesh)??throw new InvalidOperationException("无法保存展开网格。");
        using var surface=TextureMapping.CreateSurfaceParameterMapping();
        obj.SetTextureMapping(channel,storage,Transform.Identity);obj.SetTextureMapping(1,surface,Transform.Identity);
        using var actual=obj.GetTextureMapping(1,out var transform);using var stored=obj.GetTextureMapping(channel,out var sx);
        if(actual==null||stored==null)throw new InvalidOperationException("无法保存 UV 映射。");
        var record=new WorldUvRecord{Version=2,UnitScale=UnitScale(doc),GeometryCrc=obj.Geometry.DataCRC(0),Mode=method,Settings=new(){Mode=method},MappingHash=MapHash(actual,transform),MeshChannel=channel,MeshHash=MapHash(stored,sx),OrientationCorrected=corrected};
        var attrs=obj.Attributes.Duplicate();attrs.SetUserString(BackupKey,backup);attrs.SetUserString(WorldUvKey,Serialize(record));
        if(!doc.Objects.ModifyAttributes(obj.Id,attrs,true))throw new InvalidOperationException("无法保存展开记录。");
        UvRenderProvider.Refresh(doc,doc.Objects.FindId(obj.Id)!);
    }
    internal static Mesh? UnwrappedMesh(RhinoDoc doc,RhinoObject obj)
    {
        var record=ReadUv(obj);if(record is not {Version:2,MeshChannel:>1}||!UvValid(doc,obj))return null;
        using var map=obj.GetTextureMapping(record.MeshChannel);return map!=null&&map.TryGetMappingMesh(out var mesh)?mesh:null;
    }
    internal static void RemoveUvStorage(RhinoObject obj)
    {
        if(ReadUv(obj) is not {Version:2,MeshChannel:>1} r)return;
        using var stored=obj.GetTextureMapping(r.MeshChannel,out var sx);
        if(stored!=null&&r.MeshHash==MapHash(stored,sx))obj.SetTextureMapping(r.MeshChannel,null);
    }
}
