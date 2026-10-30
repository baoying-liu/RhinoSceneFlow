using Rhino;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class CatalogJob
{
    public Guid Id{get;}=Guid.NewGuid();
    public string Status{get;internal set;}="running";
    public string Stage{get;internal set;}="正在整体分析分类、名称与标签…";
    public int Count{get;internal set;}
    public string? Error{get;internal set;}
}
public static class CatalogService
{
    private static readonly Dictionary<Guid,(CatalogJob Job,CancellationTokenSource Cancel)> jobs=[];
    private static bool stopping;
    public static bool Busy=>jobs.Values.Any(v=>v.Job.Status=="running");
    public static CatalogJob Get(Guid id)=>jobs[id].Job;
    public static CatalogJob Cancel(Guid id){var j=jobs[id];j.Cancel.Cancel();return j.Job;}
    internal static void Stop(){stopping=true;foreach(var j in jobs.Values)j.Cancel.Cancel();}
    public static CatalogJob? LocalizePlants()
    {
        if(stopping||Busy||MaterialChat.Busy||MaterialGeneration.HasActiveWorkers)return null;
        var library=PlantService.Library;var snapshot=library.List().Where(a=>a.Plant!=null&&new[]{"zh","en"}.Any(k=>!a.Plant.Names.TryGetValue(k,out var name)||string.IsNullOrWhiteSpace(name))).Take(50).ToArray();if(snapshot.Length==0)return null;
        var job=new CatalogJob{Count=snapshot.Length,Stage="正在补全植物中英文名称…"};var cancel=new CancellationTokenSource();jobs.Add(job.Id,(job,cancel));
        _=Task.Run(async()=>
        {
            try
            {
                var answer=await CodexPlantAgent.RunAsync(Path.Combine(library.Root,"catalog-jobs",job.Id.ToString("N")),"localize","为已有素材补全中英文展示名称；只翻译名称，拉丁学名保持不变。",snapshot,[],cancel.Token);
                if(stopping)return;RhinoApp.InvokeOnUiThread(new Action(()=>
                {
                    try{cancel.Token.ThrowIfCancellationRequested();if(PlantService.Library.Root!=library.Root)throw new OperationCanceledException("植物库已切换。");PlantNames.Apply(library,snapshot,answer.Names);job.Status="completed";job.Stage="植物名称已更新。";}
                    catch(Exception ex){job.Status=ex is OperationCanceledException?"cancelled":"failed";job.Error=ex.Message;job.Stage=ex.Message;}
                }));
            }
            catch(Exception ex){if(!stopping)RhinoApp.InvokeOnUiThread(new Action(()=>{job.Status=ex is OperationCanceledException?"cancelled":"failed";job.Error=ex.Message;job.Stage=ex.Message;}));}
        });return job;
    }
    public static CatalogJob Organize(bool plants=false)
    {
        if(stopping||Busy||MaterialChat.Busy||MaterialGeneration.HasActiveWorkers)throw new InvalidOperationException("请先完成当前材质任务。");
        var library=plants?PlantService.Library:MaterialService.Library;var snapshot=library.List();if(snapshot.Length==0)throw new ArgumentException("素材库为空。");
        var job=new CatalogJob{Count=snapshot.Length};var cancel=new CancellationTokenSource();jobs.Add(job.Id,(job,cancel));
        _=Task.Run(async()=>
        {
            try
            {
                var directory=Path.Combine(library.Root,"catalog-jobs",job.Id.ToString("N"));
                var labels=plants?(await CodexPlantAgent.RunAsync(directory,"organize","整理植物名称与标签，分类保持已核实的科名。",snapshot,[],cancel.Token)).Items:(await CodexCatalogRunner.RunAsync(directory,"organize","整理整库；合并同义词，保留有用的材质差异。",snapshot,cancel.Token)).Items;
                if(stopping)return;RhinoApp.InvokeOnUiThread(new Action(()=>
                {
                    try{cancel.Token.ThrowIfCancellationRequested();if((plants?PlantService.Library:MaterialService.Library).Root!=library.Root)throw new InvalidOperationException("素材库已切换，请重试。");if(plants&&labels.Any(l=>l.Category!=snapshot.First(a=>a.Id==l.Id).Plant!.Family))throw new InvalidDataException("植物整理不能改写已核实的科分类。");MaterialCatalog.Apply(library,snapshot,labels);job.Status="completed";job.Stage=$"已整理 {snapshot.Length} 个素材的分类、标签和名称。";}
                    catch(Exception e){job.Status=e is OperationCanceledException?"cancelled":"failed";job.Error=e.Message;job.Stage=e.Message;}
                }));
            }
            catch(Exception e){if(!stopping)RhinoApp.InvokeOnUiThread(new Action(()=>{job.Status=e is OperationCanceledException?"cancelled":"failed";job.Error=e.Message;job.Stage=e.Message;}));}
        });return job;
    }
    internal static async Task<CatalogLabel> LabelAsync(MaterialLibrary library,MaterialAsset asset,string directory,CancellationToken cancel,string? image=null)
    {
        var catalog=library.List().Where(a=>a.Id!=asset.Id).ToArray();
        var result=await CodexCatalogRunner.RunAsync(directory,"label",asset.Prompt,[..catalog,asset],cancel,image==null?null:[image]);
        result.Randomization.Validate();result.Randomization.RecommendedMode=result.Randomization.Mode;result.Randomization.Mode="auto";result.Randomization.RecommendedBy="ai";
        return MaterialCatalog.ValidatePlan([asset],result.Items).Single() with{Randomization=result.Randomization};
    }
    internal static void SetLabel(MaterialAsset asset,CatalogLabel label){asset.Name=label.Name;asset.Category=label.Category;asset.Tags=label.Tags;if(label.Randomization!=null)asset.Randomization=MaterialLibrary.Clone(label.Randomization);}
}
