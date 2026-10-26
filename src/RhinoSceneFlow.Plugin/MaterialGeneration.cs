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
}
/// <summary>Provider-independent handoff: an attached Agent generates an image then completes
/// the job through Platform. Pending is never reported as an already generated material.</summary>
public static class MaterialGeneration
{
    private static string JobPath(Guid id)=>Path.Combine(MaterialService.Library.Root,"requests",id.ToString("N")+".json");
    public static MaterialGenerationJob Request(MaterialAsset descriptor,string prompt)
    {
        if(string.IsNullOrWhiteSpace(prompt)||prompt.Length>12000)throw new ArgumentException("请输入 1–12000 字符的材质描述。");
        var a=MaterialLibrary.Clone(descriptor);a.Maps=new(){{"baseColor","baseColor.png"}};a.Validate();a.Maps=[];
        var job=new MaterialGenerationJob{Descriptor=a,Prompt=$"Create a seamless tileable PBR base-color texture. Orthographic top-down surface only, no perspective, objects, cast shadows, ambient occlusion, specular highlights, text or watermark. Keep lighting neutral. The complete tile represents {a.WidthMeters:G8} by {a.HeightMeters:G8} meters. This is base color only; do not fabricate measured normal/roughness maps. Verify tiling with repeated previews; preserve the requested physical pattern structure. User description: {prompt}"};
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
        var job=Get(id);if(job.Status!="pending")throw new ArgumentException("此任务已完成或取消。");
        job.Descriptor.Source="ai-agent";job.Descriptor.Prompt=job.Prompt;
        var asset=MaterialService.Import(job.Descriptor,files);job.Material=asset.Id;job.Status="completed";Save(job);return asset;
    }
    public static MaterialGenerationJob Cancel(Guid id){var j=Get(id);if(j.Status!="pending")throw new ArgumentException("此任务不在等待中。");j.Status="cancelled";Save(j);return j;}
    private static void Save(MaterialGenerationJob job)
    {
        string path=JobPath(job.Id);Directory.CreateDirectory(Path.GetDirectoryName(path)!);File.WriteAllText(path+".tmp",MaterialService.Serialize(job));File.Move(path+".tmp",path,true);
    }
}
