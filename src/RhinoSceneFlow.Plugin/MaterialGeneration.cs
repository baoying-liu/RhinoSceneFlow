using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class MaterialGenerationJob
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Status { get; set; } = "pending";
    public DateTime CreatedUtc { get; set; } = DateTime.UtcNow;
    public MaterialAsset Descriptor { get; set; } = new();
    public string Prompt { get; set; } = "";
    public Guid? Material { get; set; }
    public string[] ReferenceImages { get; set; } = [];
    public string Executor { get; set; } = "agent";
    public string Error { get; set; } = "";
    public string Stage { get; set; } = "等待 Agent";
    public DateTime UpdatedUtc { get; set; } = DateTime.UtcNow;
}
/// <summary>Start runs local Codex automatically; Request retains manual Agent handoff.
/// Pending/running jobs are never reported as completed images.</summary>
public static class MaterialGeneration
{
    private static readonly Dictionary<Guid,CancellationTokenSource> workers=[];
    private static bool stopping;
    internal static bool HasActiveWorkers=>workers.Count>0;
    public static Guid? ActiveJobId=>workers.Count==0?null:workers.Keys.First();
    public static object ExecutorStatus()=>new{kind="codex-local",available=CodexImageRunner.FindExecutable()!=null,executable=CodexImageRunner.FindExecutable(),running=workers.Keys.ToArray(),authentication="Existing ChatGPT login; no API key"};
    public static MaterialGenerationJob Start(MaterialAsset descriptor,string prompt,string[]? referenceImages=null)
    {
        if(stopping)throw new InvalidOperationException("Rhino 正在关闭。");
        if(workers.Count>0)throw new InvalidOperationException("已有图片正在生成，请先完成或取消。");
        string executable=CodexImageRunner.FindExecutable()??throw new InvalidOperationException("未找到本机 Codex。请安装 Codex 或 VS Code Codex 扩展并登录；也可用 RHINOSCENEFLOW_CODEX 指定 codex.exe。");
        var job=Request(descriptor,prompt,referenceImages);job.Executor="codex-local";job.Status="running";job.Stage="正在启动本机 Codex";Save(job);
        string root=MaterialService.Library.Root;var cancel=new CancellationTokenSource();workers.Add(job.Id,cancel);
        _=Task.Run(async()=>
        {
            try
            {
                var result=await CodexImageRunner.RunAsync(executable,Path.Combine(root,"requests",job.Id.ToString("N"),"runner"),job.Prompt,job.ReferenceImages,
                    stage=>OnUi(()=>{var current=Get(job.Id);if(current.Status=="running")Progress(job.Id,stage);}),cancel.Token).ConfigureAwait(false);
                OnUi(()=>
                {
                    try{if(Get(job.Id).Status=="running")Complete(job.Id,new(){{"baseColor",result.ImagePath}});}
                    catch(Exception e){Fail(job.Id,e.Message);}
                    finally{Release(job.Id);}
                });
            }
            catch(OperationCanceledException){OnUi(()=>{if(Get(job.Id).Status=="running")Cancel(job.Id);Release(job.Id);});}
            catch(Exception e){OnUi(()=>{try{Fail(job.Id,e.Message);}finally{Release(job.Id);}});}
        });
        return job;
    }
    private static void OnUi(Action action)
    {
        if(stopping)return;
        Rhino.RhinoApp.InvokeOnUiThread((Action)(()=>{if(!stopping)action();}));
    }
    private static void Release(Guid id){if(workers.Remove(id,out var cancel))cancel.Dispose();}
    private static void Fail(Guid id,string error)
    {
        var j=Get(id);if(j.Status!="running")return;j.Status="failed";j.Error=error;j.Stage="生成失败："+error;Save(j);
    }
    internal static void StopAll()
    {
        stopping=true;
        foreach(var (id,cancel) in workers)
        {
            try{var j=Get(id);if(j.Status=="running"){j.Status="cancelled";j.Stage="Rhino 关闭，生成已停止";Save(j);}}
            catch(IOException){}
            finally{cancel.Cancel();}
        }
    }
    private static string JobPath(Guid id)=>Path.Combine(MaterialService.Library.Root,"requests",id.ToString("N")+".json");
    public static MaterialGenerationJob Request(MaterialAsset descriptor,string prompt,string[]? referenceImages=null)
    {
        if(string.IsNullOrWhiteSpace(prompt)||prompt.Length>12000)throw new ArgumentException("请输入 1–12000 字符的材质描述。");
        var a=MaterialLibrary.Clone(descriptor);a.Maps=new(){{"baseColor","baseColor.png"}};a.Validate();a.Maps=[];
        var job=new MaterialGenerationJob{Descriptor=a,Prompt=$"Create a seamless tileable PBR base-color texture. Orthographic top-down surface only, no perspective, objects, cast shadows, ambient occlusion, specular highlights, text or watermark. Keep lighting neutral. The complete tile represents {a.WidthMeters:G8} by {a.HeightMeters:G8} meters. This is base color only; do not fabricate measured normal/roughness maps. Verify tiling with repeated previews; preserve the requested physical pattern structure. User description: {prompt}"};
        var refs=referenceImages??[];if(refs.Length>8)throw new ArgumentException("最多 8 张参考图片。");
        MaterialService.ValidateImages(refs.Select((p,i)=>(p,i)).ToDictionary(t=>t.i.ToString(),t=>t.p));
        string dir=Path.Combine(MaterialService.Library.Root,"requests",job.Id.ToString("N"));
        if(refs.Length>0)Directory.CreateDirectory(dir);
        job.ReferenceImages=refs.Select((p,i)=>{string ext=Path.GetExtension(p).ToLowerInvariant();if(ext is not (".png" or ".jpg" or ".jpeg"))throw new ArgumentException("参考图只支持 PNG / JPEG。");string dest=Path.Combine(dir,i+ext);File.Copy(p,dest);return dest;}).ToArray();
        Save(job);return job;
    }
    public static MaterialGenerationJob Get(Guid id)
    {
        var job=MaterialService.Deserialize<MaterialGenerationJob>(File.ReadAllText(JobPath(id)));
        if(!stopping&&job.Executor=="codex-local"&&job.Status=="running"&&!workers.ContainsKey(id))
        {job.Status="failed";job.Error="上次生成执行端已结束，请重新生成。";job.Stage=job.Error;Save(job);}
        return job;
    }
    public static MaterialGenerationJob[] List()
    {
        string directory=Path.Combine(MaterialService.Library.Root,"requests");return !Directory.Exists(directory)?[]:
            Directory.EnumerateFiles(directory,"*.json").Select(p=>Get(Guid.Parse(Path.GetFileNameWithoutExtension(p)))).OrderByDescending(j=>j.CreatedUtc).ToArray();
    }
    public static MaterialAsset Complete(Guid id,Dictionary<string,string> files)
    {
        var job=Get(id);if(job.Status is not ("pending" or "running"))throw new ArgumentException("此任务已完成或取消。");
        job.Descriptor.Source="ai-agent";job.Descriptor.Prompt=job.Prompt;
        var asset=MaterialService.Import(job.Descriptor,files);job.Material=asset.Id;job.Status="completed";job.Stage="生成完成，已入库";Save(job);return asset;
    }
    public static MaterialGenerationJob Cancel(Guid id){var j=Get(id);if(j.Status is not ("pending" or "running"))throw new ArgumentException("此任务不在等待中。");j.Status="cancelled";j.Stage="已取消";Save(j);if(workers.TryGetValue(id,out var cancel))cancel.Cancel();return j;}
    public static MaterialGenerationJob Progress(Guid id,string stage)
    {
        var j=Get(id);if(j.Status is not ("pending" or "running"))throw new ArgumentException("任务已结束。");
        if(string.IsNullOrWhiteSpace(stage)||stage.Length>200)throw new ArgumentException("状态需为 1–200 字符。");
        j.Status="running";j.Stage=stage;Save(j);return j;
    }
    private static void Save(MaterialGenerationJob job)
    {
        job.UpdatedUtc=DateTime.UtcNow;string path=JobPath(job.Id);Directory.CreateDirectory(Path.GetDirectoryName(path)!);File.WriteAllText(path+".tmp",MaterialService.Serialize(job));File.Move(path+".tmp",path,true);
    }
}
