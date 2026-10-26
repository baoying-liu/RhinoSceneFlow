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
    public string Stage { get; set; } = "等待 Agent";
    public DateTime UpdatedUtc { get; set; } = DateTime.UtcNow;
}
/// <summary>Provider-independent handoff: an attached Agent generates an image then completes
/// the job through Platform. Pending is never reported as an already generated material.</summary>
public static class MaterialGeneration
{
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
    public static MaterialGenerationJob Get(Guid id)=>MaterialService.Deserialize<MaterialGenerationJob>(File.ReadAllText(JobPath(id)));
    public static MaterialGenerationJob[] List()
    {
        string directory=Path.Combine(MaterialService.Library.Root,"requests");return !Directory.Exists(directory)?[]:
            Directory.EnumerateFiles(directory,"*.json").Select(p=>MaterialService.Deserialize<MaterialGenerationJob>(File.ReadAllText(p))).OrderByDescending(j=>j.CreatedUtc).ToArray();
    }
    public static MaterialAsset Complete(Guid id,Dictionary<string,string> files)
    {
        var job=Get(id);if(job.Status is not ("pending" or "running"))throw new ArgumentException("此任务已完成或取消。");
        job.Descriptor.Source="ai-agent";job.Descriptor.Prompt=job.Prompt;
        var asset=MaterialService.Import(job.Descriptor,files);job.Material=asset.Id;job.Status="completed";job.Stage="生成完成，已入库";Save(job);return asset;
    }
    public static MaterialGenerationJob Cancel(Guid id){var j=Get(id);if(j.Status is not ("pending" or "running"))throw new ArgumentException("此任务不在等待中。");j.Status="cancelled";j.Stage="已取消";Save(j);return j;}
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
