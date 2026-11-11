using System.Collections.Concurrent;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Rhino;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class RandomTextureJob
{
    public Guid Id{get;}=Guid.NewGuid();
    public string Status{get;internal set;}="running";
    public string Stage{get;internal set;}="正在准备随机贴图";
    public int Percent{get;internal set;}
    public string? Error{get;internal set;}
}
internal sealed record RandomTextureView(string Key,Dictionary<string,string> Maps,double WidthMeters,double HeightMeters);
public static class RandomTextureService
{
    private sealed record Entry(RandomTextureJob Job,CancellationTokenSource Cancel,uint Document);
    private static readonly Dictionary<Guid,Entry> jobs=[];
    private static readonly ConcurrentDictionary<string,TextureBakeManifest> manifests=new();
    private static bool stopping;
    public static bool Busy=>jobs.Values.Any(v=>v.Job.Status=="running");
    public static RandomTextureJob Get(Guid id)=>jobs[id].Job;
    public static RandomTextureJob Cancel(Guid id){var value=jobs[id];value.Cancel.Cancel();return value.Job;}
    internal static void CancelDocument(uint document){foreach(var e in jobs.Values.Where(v=>v.Document==document&&v.Job.Status=="running"))e.Cancel.Cancel();}
    internal static void Stop(){stopping=true;foreach(var e in jobs.Values)e.Cancel.Cancel();}
    private static void Ui(Action action){if(!stopping)RhinoApp.InvokeOnUiThread(new Action(()=>{if(!stopping)action();}));}
    private static TextureBakeRequest Request(MaterialLibrary library,MaterialAsset asset,Guid instance)
    {
        int seed=asset.Randomization.InstanceSeed(instance);
        string json=JsonSerializer.Serialize(new{version=1,asset.Id,asset.Revision,asset.WidthMeters,asset.HeightMeters,asset.Sha256,asset.Randomization,seed},MaterialLibrary.Json);
        string key=Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(json)));
        return new(){Key=key,Maps=asset.Maps.Keys.Where(MaterialLibrary.Slots.Contains).ToDictionary(s=>s,s=>library.MapPath(asset,s)),Sha256=asset.Sha256.Where(p=>MaterialLibrary.Slots.Contains(p.Key)).ToDictionary(p=>p.Key,p=>p.Value),Settings=MaterialLibrary.Clone(asset.Randomization),Seed=seed,WidthMeters=asset.WidthMeters,HeightMeters=asset.HeightMeters,OutputDirectory=Path.Combine(library.Root,"cache","random-v1",asset.Id.ToString("N"),key[..24])};
    }
    private static TextureBakeManifest? Cached(TextureBakeRequest request)
    {
        if(manifests.TryGetValue(request.OutputDirectory,out var cached)&&cached.Maps.Values.All(m=>File.Exists(Path.Combine(request.OutputDirectory,m))))return cached;
        string path=Path.Combine(request.OutputDirectory,"manifest.json");if(!File.Exists(path))return null;
        var value=JsonSerializer.Deserialize<TextureBakeManifest>(File.ReadAllText(path),MaterialLibrary.Json)??throw new InvalidDataException("随机缓存无效。");
        int span=request.Settings.ResolvedMode=="object"?1:request.Settings.Tiles;
        if(value.Version!=1||value.Key!=request.Key||value.WidthMeters!=request.WidthMeters*span||value.HeightMeters!=request.HeightMeters*span||!value.Maps.Keys.ToHashSet().SetEquals(request.Maps.Keys))throw new InvalidDataException("随机缓存尺寸或身份不匹配。");
        foreach(var (slot,file) in value.Maps)
        {
            if(Path.GetFileName(file)!=file||!file.StartsWith(request.Key[..24]+"_",StringComparison.Ordinal)||!value.Sha256.TryGetValue(slot,out var hash)||RandomImage.Hash(Path.Combine(request.OutputDirectory,file))!=hash)throw new InvalidDataException("随机缓存校验失败，请使用新种子重新准备。");
        }
        manifests[request.OutputDirectory]=value;return value;
    }
    internal static RandomTextureView? TryResolve(MaterialLibrary library,MaterialAsset asset,Guid instance)
    {
        if(asset.Seasonal.Variants.Values.Any(v=>v.Elevation!=null&&v.Elevation!="baseColor"))
        {
            string slot=Seasons.Slot(asset,PlantService.CurrentSeason);
            if(asset.Randomization.ResolvedMode=="off")return new("",asset.Maps.Keys.Where(MaterialLibrary.Slots.Contains).ToDictionary(s=>s,s=>library.MapPath(asset,s=="baseColor"?slot:s)),asset.WidthMeters,asset.HeightMeters);
            var seasonal=SeasonRequest(library,asset,slot,instance);var baked=Cached(seasonal);return baked==null?null:new(Request(library,asset,instance).Key,baked.Maps.ToDictionary(p=>p.Key,p=>Path.Combine(seasonal.OutputDirectory,p.Value)),baked.WidthMeters,baked.HeightMeters);
        }
        if(asset.Randomization.ResolvedMode=="off")return new("",asset.Maps.Keys.Where(MaterialLibrary.Slots.Contains).ToDictionary(s=>s,s=>library.MapPath(asset,s)),asset.WidthMeters,asset.HeightMeters);
        var request=Request(library,asset,instance);var cache=Cached(request);
        return cache==null?null:new(cache.Key,cache.Maps.ToDictionary(p=>p.Key,p=>Path.Combine(request.OutputDirectory,p.Value)),cache.WidthMeters,cache.HeightMeters);
    }
    internal static RandomTextureView Resolve(MaterialAsset asset,Guid instance)=>TryResolve(MaterialService.Library,asset,instance)??throw new InvalidOperationException("请先准备此材质的随机贴图，或通过工具面板应用以自动准备。");
    private static TextureBakeRequest SeasonRequest(MaterialLibrary library,MaterialAsset source,string slot,Guid instance)
    {
        var a=MaterialLibrary.Clone(source);a.Maps["baseColor"]=source.Maps[slot];a.Sha256["baseColor"]=source.Sha256[slot];var r=Request(library,a,instance);
        // Metadata/aliases and FollowSeason do not change a random texture bake.
        string data=JsonSerializer.Serialize(new{version=2,a.Id,a.WidthMeters,a.HeightMeters,r.Sha256,a.Randomization,r.Seed},MaterialLibrary.Json);
        r.Key=Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(data)));r.OutputDirectory=Path.Combine(library.Root,"cache","random-v1",a.Id.ToString("N"),r.Key[..24]);return r;
    }
    internal static string SeasonalPath(MaterialAsset asset,string slot,Guid instance,bool randomized)
    {
        var library=MaterialService.Library;if(!randomized||asset.Randomization.ResolvedMode=="off")return library.MapPath(asset,slot);
        var r=SeasonRequest(library,asset,slot,asset.Randomization.ResolvedMode=="object"?instance:Guid.Empty);var cached=Cached(r)??throw new InvalidOperationException("季节随机贴图尚未准备，请在素材的季节版本中点击补齐；不会重复生成已有图片。");return Path.Combine(r.OutputDirectory,cached.Maps["baseColor"]);
    }
    internal static Guid[] SeasonalInstances(Guid asset)
    {
        var ids=new HashSet<Guid>{Guid.Empty};
        foreach(var doc in RhinoDoc.OpenDocuments())foreach(var obj in doc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.AnyObject))
        {
            bool layer=obj.Attributes.MaterialSource==Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer;var l=doc.Layers[obj.Attributes.LayerIndex];string? text=layer?l.GetUserString(MaterialService.BindingKey):obj.Attributes.GetUserString(MaterialService.BindingKey);
            if(text!=null&&MaterialService.Deserialize<MaterialBinding>(text).Asset==asset)ids.Add(layer?l.Id:obj.Id);
        }
        return ids.ToArray();
    }
    internal static async Task PrepareSeasons(MaterialLibrary library,MaterialAsset asset,Guid[] instances,string work,CancellationToken token,Action<string> progress)
    {
        if(asset.Randomization.ResolvedMode=="off")return;
        var slots=asset.Seasonal.Variants.Values.Select(v=>v.Elevation).Where(s=>s!=null).Select(s=>s!).Append("baseColor").Distinct().ToArray();if(slots.All(s=>s=="baseColor"))return;
        foreach(string slot in slots)foreach(Guid instance in asset.Randomization.ResolvedMode=="object"?instances:new[]{Guid.Empty})
        {
            token.ThrowIfCancellationRequested();var r=SeasonRequest(library,asset,slot,instance);if(Cached(r)!=null)continue;
            string exe=Path.Combine(Path.GetDirectoryName(typeof(RandomTextureService).Assembly.Location)!,"TextureWorker","SceneFlow.TextureWorker.exe");if(!File.Exists(exe))throw new FileNotFoundException("缺少随机贴图 Worker。",exe);
            string path=Path.Combine(work,"season-bake-"+r.Key[..24]+".json");await File.WriteAllTextAsync(path,JsonSerializer.Serialize(r,MaterialLibrary.Json),token);
            using var child=new Process{StartInfo=new(exe){UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true}};child.StartInfo.ArgumentList.Add(path);child.Start();
            void Kill(){try{if(!child.HasExited)child.Kill(true);}catch(InvalidOperationException){}catch(System.ComponentModel.Win32Exception){}}
            using var timeout=CancellationTokenSource.CreateLinkedTokenSource(token);timeout.CancelAfter(TimeSpan.FromMinutes(10));using var stop=timeout.Token.Register(Kill);var error=child.StandardError.ReadToEndAsync();
            try{while(await child.StandardOutput.ReadLineAsync(timeout.Token) is {} line){var parts=line.Split(' ');if(parts.Length==5&&parts[0]=="PROGRESS"&&double.TryParse(parts[2],out var done)&&double.TryParse(parts[3],out var total)&&total>0)progress($"准备季节随机贴图 · {Math.Clamp(done/total*100,0,100):F0}%");}await child.WaitForExitAsync(timeout.Token);if(child.ExitCode!=0)throw new InvalidOperationException("季节随机贴图失败："+await error);if(Cached(r)==null)throw new InvalidDataException("季节随机缓存不完整。");}
            finally{Kill();}
        }
    }
    internal static Guid[] Instances(MaterialAsset asset,Guid[] objects,Guid[]? layers)=>asset.Randomization.ResolvedMode=="object"?objects.Concat(layers??[]).Append(Guid.Empty).Distinct().ToArray():[Guid.Empty];
    internal static bool Ready(MaterialAsset asset,Guid[] objects,Guid[]? layers)=>Instances(asset,objects,layers).All(id=>TryResolve(MaterialService.Library,asset,id)!=null);
    public static RandomTextureJob Start(RhinoDoc doc,Guid assetId,Guid[]? objects=null,Guid[]? layers=null,bool preview=false)
    {
        NamedViewExportService.RequireActive(doc);if(stopping)throw new InvalidOperationException("Rhino 正在关闭。");
        var library=MaterialService.Library;var asset=library.Get(assetId);library.Verify(asset);
        var ids=preview?[]:MaterialService.ResolveTargets(doc,objects,layers);
        var requests=Instances(asset,ids,layers).Where(_=>asset.Randomization.ResolvedMode!="off").Select(id=>Request(library,asset,id)).ToArray();
        uint serial=doc.RuntimeSerialNumber;var cancel=new CancellationTokenSource();var job=new RandomTextureJob();jobs.Add(job.Id,new(job,cancel,serial));
        string exe=Path.Combine(Path.GetDirectoryName(typeof(RandomTextureService).Assembly.Location)!,"TextureWorker","SceneFlow.TextureWorker.exe");
        string work=Path.Combine(library.Root,"cache","random-jobs",job.Id.ToString("N"));
        _=Task.Run(async()=>
        {
            try
            {
                Directory.CreateDirectory(work);int done=0;
                foreach(var request in requests)
                {
                    cancel.Token.ThrowIfCancellationRequested();
                    if(Cached(request)==null)
                    {
                        if(!File.Exists(exe))throw new FileNotFoundException("缺少随机贴图 Worker，请安装完整插件包。",exe);
                        string path=Path.Combine(work,"request-"+done+".json");await File.WriteAllTextAsync(path,JsonSerializer.Serialize(request,MaterialLibrary.Json),cancel.Token);
                        using var child=new Process{StartInfo=new(exe){UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true}};child.StartInfo.ArgumentList.Add(path);child.Start();
                        void Kill(){try{if(!child.HasExited)child.Kill(true);}catch(InvalidOperationException){}catch(System.ComponentModel.Win32Exception){}}
                        using var timeout=CancellationTokenSource.CreateLinkedTokenSource(cancel.Token);timeout.CancelAfter(TimeSpan.FromMinutes(10));using var stop=timeout.Token.Register(Kill);
                        var error=child.StandardError.ReadToEndAsync();
                        try
                        {
                            while(await child.StandardOutput.ReadLineAsync(timeout.Token) is {} line)
                            {
                                int index=done;int rowPercent=-1;string stage=line;
                                var parts=line.Split(' ');
                                if(parts.Length==5&&parts[0]=="PROGRESS"&&int.TryParse(parts[1],out int map)&&int.TryParse(parts[2],out int rows)&&int.TryParse(parts[3],out int total)&&int.TryParse(parts[4],out int maps)&&total>0&&maps>0)
                                {rowPercent=Math.Min(99,(int)(100*(index+(map+(double)rows/total)/maps)/requests.Length));stage=$"通道 {map+1}/{maps} · {rows}/{total} 行";}
                                Ui(()=>{if(job.Status!="running")return;job.Stage=$"随机贴图 {index+1}/{requests.Length} · {stage}";if(rowPercent>=0)job.Percent=Math.Max(job.Percent,rowPercent);});
                            }
                            await child.WaitForExitAsync(timeout.Token);if(child.ExitCode!=0){string details=await error;await File.WriteAllTextAsync(Path.Combine(work,"worker-error.txt"),details);throw new InvalidOperationException("随机贴图准备失败："+details.Split('\n').FirstOrDefault()?.Trim());}
                        }
                        catch(OperationCanceledException) when(!cancel.IsCancellationRequested){throw new TimeoutException("随机贴图 Worker 超时，未应用。请缩小周期后重试。");}
                        finally{Kill();}
                        if(Cached(request)==null)throw new InvalidDataException("Worker 未生成完整随机缓存。");
                    }
                    done++;int percent=Math.Min(99,done*100/Math.Max(1,requests.Length));Ui(()=>{if(job.Status=="running")job.Percent=Math.Max(job.Percent,percent);});
                }
                await PrepareSeasons(library,asset,Instances(asset,ids,layers),work,cancel.Token,s=>Ui(()=>job.Stage=s));
                Ui(()=>
                {
                    try
                    {
                        cancel.Token.ThrowIfCancellationRequested();var current=RhinoDoc.FromRuntimeSerialNumber(serial);
                        if(current==null||current.IsClosing||MaterialService.Library.Root!=library.Root||library.Get(assetId).Revision!=asset.Revision)throw new OperationCanceledException("文档或材质已变化，未应用。");
                        if(!preview&&!MaterialService.ResolveTargets(current,objects,layers).ToHashSet().SetEquals(ids))throw new InvalidOperationException("处理期间目标对象已变化，请重新应用。");
                        job.Status="completed";job.Percent=100;job.Stage="随机贴图已准备，可按真实尺寸应用。";
                    }
                    catch(Exception e){job.Status=e is OperationCanceledException?"cancelled":"failed";job.Stage=e.Message;job.Error=e.Message;}
                });
            }
            catch(Exception e){Ui(()=>{job.Status=e is OperationCanceledException?"cancelled":"failed";job.Stage=e is OperationCanceledException?"随机贴图准备已停止，未应用。":e.Message;job.Error=e.Message;});}
        });return job;
    }
}
