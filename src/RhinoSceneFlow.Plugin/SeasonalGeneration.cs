using Rhino;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class SeasonalJob
{
    public Guid Id{get;}=Guid.NewGuid();
    public Guid Asset{get;init;}
    public string Status{get;internal set;}="running";
    public string Stage{get;internal set;}="检查已有季节版本";
    public string? Error{get;internal set;}
    public int Completed{get;internal set;}
}
public static class SeasonalGeneration
{
    private static volatile bool stopping;
    public static bool Busy=>jobs.Values.Any(v=>v.Job.Status=="running");
    private static readonly System.Collections.Concurrent.ConcurrentDictionary<Guid,(SeasonalJob Job,CancellationTokenSource Cancel)> jobs=new();
    public static SeasonalJob Status(Guid id)=>jobs.TryGetValue(id,out var j)?j.Job:throw new ArgumentException("季节任务不存在。");
    public static SeasonalJob Cancel(Guid id){if(jobs.TryGetValue(id,out var j)&&j.Job.Status=="running")j.Cancel.Cancel();return Status(id);}
    internal static void Stop(){stopping=true;foreach(var j in jobs.Values)if(j.Job.Status=="running")j.Cancel.Cancel();}
    public static SeasonalJob Start(Guid assetId,bool plant,bool fourSeasons=true)
    {
        if(stopping)throw new OperationCanceledException();
        var library=plant?PlantService.Library:MaterialService.Library;var asset=library.Get(assetId);library.Verify(asset);
        if((asset.Plant!=null)!=plant)throw new ArgumentException("素材类型不一致。");
        if(jobs.Values.Any(j=>j.Job.Asset==assetId&&j.Job.Status=="running"))throw new InvalidOperationException("此素材的季节任务正在进行。");
        var preferences=PluginPreferences.Load();string directory=Path.Combine(library.Root,"season-jobs",Guid.NewGuid().ToString("N"));Directory.CreateDirectory(directory);
        var requested=(fourSeasons?Seasons.All:new[]{"summer"});bool complete=requested.All(s=>Seasons.Has(asset,s)&&(!plant||Seasons.Has(asset,s,true)));var instances=plant?Array.Empty<Guid>():RandomTextureService.SeasonalInstances(assetId);
        var job=new SeasonalJob{Asset=assetId};var cancel=new CancellationTokenSource();jobs[job.Id]=(job,cancel);
        _=Task.Run(async()=>
        {
            try
            {
                if(complete){await RandomTextureService.PrepareSeasons(library,asset,instances,directory,cancel.Token,s=>job.Stage=s);job.Completed=requested.Length*(plant?2:1);job.Status="completed";job.Stage="所需版本已存在，已复用；随机缓存已就绪";return;}
                var token=cancel.Token;string original=library.MapPath(asset,"baseColor");
                string reference=Path.Combine(directory,"summer"+Path.GetExtension(original));File.Copy(original,reference);
                var answer=await CodexPlantAgent.RunAsync(Path.Combine(directory,"plan"),"seasons",System.Text.Json.JsonSerializer.Serialize(asset,MaterialLibrary.Json)+"\nClimate: "+preferences.Climate,[asset],[reference],token);
                if(!plant)answer.CrownWidthMeters=3;
                if(!double.IsFinite(answer.CrownWidthMeters)||answer.CrownWidthMeters<=0||answer.CrownWidthMeters>1000)throw new InvalidDataException("AI 冠幅无效。");
                var aliases=answer.SeasonPlan;if(aliases.Length!=4||aliases.Select(a=>a.Season).Distinct().Count()!=4||aliases.Any(a=>!Seasons.All.Contains(a.Season)||a.SourceSeason!="summer"&&a.SourceSeason!=a.Season))throw new InvalidDataException("AI 季节计划无效。");
                asset.Seasonal.Climate=preferences.Climate;asset=library.Update(asset);
                if(!Seasons.Has(asset,"summer"))asset=library.AddSeason(asset.Id,asset.Revision,"summer",false,null,"baseColor");
                foreach(string season in new[]{"summer","spring","autumn","winter"}.Take(fourSeasons?4:1))
                {
                    token.ThrowIfCancellationRequested();bool same=season!="summer"&&(!answer.Seasonal||aliases.Single(a=>a.Season==season).SourceSeason=="summer");
                    foreach(bool plan in plant?new[]{false,true}:new[]{false})
                    {
                        token.ThrowIfCancellationRequested();if(Seasons.Has(asset,season,plan)){job.Completed++;continue;}
                        job.Stage=$"{Seasons.Name(season)}季 · {(plan?"平面":"立面/底色")}";
                        if(same){var summer=asset.Seasonal.Variants["summer"];asset=library.AddSeason(asset.Id,asset.Revision,season,plan,null,(plan?summer.Plan:summer.Elevation)!,answer.CrownWidthMeters);job.Completed++;continue;}
                        string system=plant?
                            "Generate exactly one NEW botanical PNG with real transparent alpha using ONLY image_gen transparent_background:true. No shell/web/MCP/APIs. Return fresh imagePath. Same exact verified species, cultivar, specimen shape, branch structure and scale as reference. No scene, ground, pot, text, watermark or cast shadow. Entire crown fits with a small transparent margin. " + (plan?"Strict orthographic TOP-DOWN crown plan, no visible elevation trunk, crown centred. Horizontal botanical cutout.":"Orthographic ELEVATION, entire plant from root base to crown, base centred at bottom. Keep the same framing and root anchor as summer reference."):
                            "Use ONLY image_gen to create one NEW seamless, tileable surface base-color PNG. No shell/web/MCP/APIs. Preserve the reference material identity, exact pattern alignment, scale, physical tile size and structures. Change seasonal appearance only, no lighting/cast shadows or scene. Return a fresh imagePath.";
                        var refs=new List<string>{reference};if(plan&&Seasons.Has(asset,"summer",true))refs.Add(library.MapPath(asset,asset.Seasonal.Variants["summer"].Plan!));
                        var result=await CodexMaterialChatRunner.RunAsync(Path.Combine(directory,season+(plan?"-plan":"-elevation")),"Asset: "+asset.Name+"\nVerified taxon: "+asset.Plant?.ScientificName+"\nTarget season: "+season+"\nClimate: "+preferences.Climate+"\nSeason reasoning: "+aliases.Single(a=>a.Season==season).Reason,refs.ToArray(),s=>job.Stage=s,token,system);
                        if(result.ImagePath==null)throw new InvalidOperationException("没有生成新的季节图片："+result.Reply);
                        using(var bitmap=new System.Drawing.Bitmap(result.ImagePath))
                        {
                            if(bitmap.Width>8192||bitmap.Height>8192)throw new InvalidDataException("季节图片超过 8192 像素。");
                            if(plant){int clear=0,solid=0;for(int y=0;y<bitmap.Height;y+=Math.Max(1,bitmap.Height/256))for(int x=0;x<bitmap.Width;x+=Math.Max(1,bitmap.Width/256)){if(bitmap.GetPixel(x,y).A<2)clear++;else solid++;}if(clear<16||solid<16)throw new InvalidDataException("植物季节图需要真实透明背景和可见植株。");}
                        }
                        string path=result.ImagePath;double? width=null,anchor=null;
                        if(plant){var normalized=PlantCutout.Normalize(path,Path.Combine(directory,season+(plan?"-plan":"-elevation")+"-normalized.png"),asset.HeightMeters);path=normalized.Path;if(!plan){width=normalized.Width;anchor=normalized.Anchor;}}
                        token.ThrowIfCancellationRequested();asset=library.AddSeason(asset.Id,asset.Revision,season,plan,path,null,answer.CrownWidthMeters,width,anchor);job.Completed++;
                    }
                }
                await RandomTextureService.PrepareSeasons(library,asset,instances,directory,cancel.Token,s=>job.Stage=s);
                job.Status="completed";job.Stage=fourSeasons?"四季版本已就绪（相同季节共用图片）":"夏季立面与平面已就绪";
            }
            catch(Exception e){job.Status=e is OperationCanceledException?"cancelled":"failed";job.Error=e.Message;job.Stage="已保存的版本保留；"+e.Message;}
            finally{if(!stopping)RhinoApp.InvokeOnUiThread(new Action(PlantService.RefreshSeasons));}
        });return job;
    }
}
