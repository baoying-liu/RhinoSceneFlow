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
    private sealed record Input(Guid Id,uint Crc,string MappingState,string Backup,Point3d Origin,double Scale,Vec3[] Points,Vec3[] Normals,int[] Indices);
    private static readonly Dictionary<Guid,(UnwrapJob Job,CancellationTokenSource Cancel)> jobs=[];
    private static bool stopping;
    public static UnwrapJob Get(Guid id)=>jobs.TryGetValue(id,out var value)?value.Job:throw new ArgumentException("展开任务不存在。");
    public static object Cancel(Guid id){if(jobs.TryGetValue(id,out var value)&&value.Job.Status=="running"){value.Cancel.Cancel();value.Job.Stage="正在取消 xatlas";}return Get(id);}
    internal static void StopAll(){stopping=true;foreach(var value in jobs.Values.Where(v=>v.Job.Status=="running"))value.Cancel.Cancel();}
    private static void Ui(Action action){if(!stopping)RhinoApp.InvokeOnUiThread(new Action(()=>{if(!stopping)action();}));}
    public static UnwrapJob Start(RhinoDoc doc,Guid[]? objects,Guid[]? layers)
    {
        if(stopping)throw new InvalidOperationException("Rhino 正在关闭。");
        if(jobs.Values.Any(v=>v.Job.Status=="running"))throw new InvalidOperationException("已有 xatlas 任务正在运行。");
        string executable=Path.Combine(Path.GetDirectoryName(typeof(UnwrapService).Assembly.Location)!,"SceneFlow.UvWorker.exe");
        if(!File.Exists(executable))throw new FileNotFoundException("请安装包含 C++ xatlas worker 的完整插件包。",executable);
        double scale=MaterialService.UnitScale(doc);var ids=MaterialService.ResolveTargets(doc,objects,layers);uint serial=doc.RuntimeSerialNumber;
        var clock=System.Diagnostics.Stopwatch.StartNew();var inputs=ids.Select(id=>Capture(doc.Objects.FindId(id)!,scale)).ToArray();var job=new UnwrapJob();var cancel=new CancellationTokenSource();jobs.Add(job.Id,(job,cancel));
        _=Task.Run(async()=>
        {
            try
            {
                var results=new List<UvUnwrapResult>();
                for(int i=0;i<inputs.Length;i++)
                {
                    int item=i;var input=inputs[i];
                    results.Add(await XatlasRunner.RunAsync(executable,input.Points,input.Indices,(stage,n)=>Ui(()=>{job.Stage=$"xatlas {item+1}/{inputs.Length} · {stage}";job.Percent=(item*100+n)/inputs.Length;}),cancel.Token));
                }
                Ui(()=>
                {
                    try
                    {
                        cancel.Token.ThrowIfCancellationRequested();var current=RhinoDoc.FromRuntimeSerialNumber(serial)??throw new InvalidOperationException("原文档已关闭。");
                        foreach(var input in inputs)
                        {
                            var obj=current.Objects.FindId(input.Id)??throw new InvalidOperationException("原物件已删除。");
                            if(obj.Geometry.DataCRC(0)!=input.Crc||MaterialService.UnitScale(current)!=input.Scale||MaterialService.UnwrapMappingState(obj)!=input.MappingState)throw new InvalidOperationException("计算期间物件、单位或 UV 已改变，结果未应用，请重新展开。");
                        }
                        var previous=inputs.Select(input=>
                        {
                            var o=current.Objects.FindId(input.Id)!;var map=o.GetTextureMapping(1,out var x);
                            return (Id:input.Id,Attributes:o.Attributes.Duplicate(),Map:map,Transform:x);
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
                                touched=i+1;MaterialService.CommitUnwrapped(current,current.Objects.FindId(input.Id)!,mesh,input.Backup);
                            }
                        }
                        catch
                        {
                            foreach(var p in previous.Take(touched))
                            {
                                var o=current.Objects.FindId(p.Id)!;o.SetTextureMapping(1,p.Map,p.Transform);current.Objects.ModifyAttributes(p.Id,p.Attributes,true);
                            }
                            throw;
                        }
                        finally{foreach(var p in previous){p.Map?.Dispose();p.Attributes.Dispose();}if(undo!=0)current.EndUndoRecord(undo);}
                        job.Results=inputs.Select((input,i)=>(object)new{input.Id,triangles=inputs[i].Indices.Length/3,vertices=results[i].SourceVertices.Length,charts=results[i].Charts,surfaceAreaMeters2=results[i].SurfaceArea,uvAreaMeters2=results[i].UvArea,stretchMedian=results[i].StretchMedian,stretch95=results[i].Stretch95,stretchMax=results[i].StretchMax,repairedTriangles=results[i].RepairedTriangles,rawStretchMax=results[i].RawStretchMax}).ToArray();
                        job.Seconds=clock.Elapsed.TotalSeconds;job.Status="completed";job.Percent=100;job.Stage="展开完成 · 1 UV 单位 = 1 米（面积校准）";current.Views.Redraw();
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
        mesh.Vertices.CombineIdentical(true,true);mesh.Faces.ConvertQuadsToTriangles();mesh.Faces.CullDegenerateFaces();mesh.Vertices.CullUnused();mesh.Normals.ComputeNormals();
        var origin=mesh.GetBoundingBox(true).Center;var points=mesh.Vertices.Select(v=>new Vec3((v.X-origin.X)/scale,(v.Y-origin.Y)/scale,(v.Z-origin.Z)/scale)).ToArray();
        var normals=mesh.Normals.Select(n=>new Vec3(n.X,n.Y,n.Z)).ToArray();var indices=mesh.Faces.SelectMany(f=>new[]{f.A,f.B,f.C}).ToArray();
        return new(obj.Id,obj.Geometry.DataCRC(0),MaterialService.UnwrapMappingState(obj),MaterialService.UnwrapBackup(obj),origin,scale,points,normals,indices);
    }
}

public static partial class MaterialService
{
    internal static string UnwrapBackup(RhinoObject obj)=>Backup(obj);
    internal static string UnwrapMappingState(RhinoObject obj){using var m=obj.GetTextureMapping(1,out var x);return m==null?"none":MapHash(m,x);}
    internal static void CommitUnwrapped(RhinoDoc doc,RhinoObject obj,Mesh mesh,string backup)
    {
        using var map=TextureMapping.CreateCustomMeshMapping(mesh)??throw new InvalidOperationException("无法创建原生自定义 UV 映射。");
        obj.SetTextureMapping(1,map,Transform.Identity);using var actual=obj.GetTextureMapping(1,out var transform);
        if(actual==null)throw new InvalidOperationException("无法保存 xatlas 映射。");
        var record=new WorldUvRecord{UnitScale=UnitScale(doc),GeometryCrc=obj.Geometry.DataCRC(0),Mode="xatlas",Settings=new(){Mode="xatlas"},MappingHash=MapHash(actual,transform)};
        var attrs=obj.Attributes.Duplicate();attrs.SetUserString(BackupKey,backup);attrs.SetUserString(WorldUvKey,Serialize(record));
        if(!doc.Objects.ModifyAttributes(obj.Id,attrs,true))throw new InvalidOperationException("无法保存展开记录。");
    }
    internal static Mesh? UnwrappedMesh(RhinoDoc doc,RhinoObject obj)
    {
        if(ReadUv(obj)?.Mode!="xatlas"||!UvValid(doc,obj))return null;
        using var map=obj.GetTextureMapping(1);return map!=null&&map.TryGetMappingMesh(out var mesh)?mesh:null;
    }
}
