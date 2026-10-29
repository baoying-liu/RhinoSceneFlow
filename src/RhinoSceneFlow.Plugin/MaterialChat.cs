using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Text.Json;
using Eto.Forms;
using Rhino;
using RhinoSceneFlow.Core;
using Microsoft.Web.WebView2.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class MaterialChatJob
{
    public Guid Id{get;}=Guid.NewGuid();
    public string Kind{get;internal set;}="material";
    public string Status{get;internal set;}="running";
    public string Stage{get;internal set;}="正在连接本机 Codex";
    public string? Reply{get;internal set;}
    public string? Error{get;internal set;}
    public Guid? Material{get;internal set;}
    public Guid? Plant{get;internal set;}
    public CatalogMatch[] PlantMatches{get;internal set;}=[];
    public CatalogMatch[] Matches{get;internal set;}=[];
    public string? ImagePath{get;internal set;}
}
public static class MaterialChat
{
    private static readonly Dictionary<Guid,MaterialChatJob> jobs=[];
    private static readonly Dictionary<Guid,CancellationTokenSource> workers=[];
    private static bool stopping;
    internal static bool Busy=>workers.Count>0;
    public static MaterialChatJob Get(Guid id)=>jobs.TryGetValue(id,out var job)?job:throw new ArgumentException("对话任务不存在。");
    public static object Cancel(Guid id){if(workers.TryGetValue(id,out var cancel))cancel.Cancel();return Get(id);}
    internal static void StopAll(){stopping=true;foreach(var worker in workers.Values)worker.Cancel();}
    private static void Ui(Action action){if(!stopping)RhinoApp.InvokeOnUiThread(new Action(()=>{if(!stopping)action();}));}
    public static MaterialChatJob Start(string conversation,string[] references,double widthMeters=1,double heightMeters=1,bool reuseSimilar=true)
    {
        if(stopping||Busy||MaterialGeneration.HasActiveWorkers||CatalogService.Busy)throw new InvalidOperationException("请先完成或取消当前对话 / 生成任务。");
        if(string.IsNullOrWhiteSpace(conversation)||conversation.Length>64000)throw new ArgumentException("对话长度需为 1–64000 字符。");
        if(references.Length>8)throw new ArgumentException("最多 8 张参考图。");
        MaterialService.ValidateImages(references.Select((p,i)=>(p,i)).ToDictionary(t=>t.i.ToString(),t=>t.p));
        var asset=new MaterialAsset{Name="AI 对话材质 "+DateTime.Now.ToString("HHmmss"),WidthMeters=widthMeters,HeightMeters=heightMeters,Source="ai-agent",Prompt=conversation};
        var validation=MaterialLibrary.Clone(asset);validation.Maps=new(){{"baseColor","baseColor.png"}};validation.Validate();
        string directory=Path.Combine(MaterialService.Library.Root,"chat-jobs",Guid.NewGuid().ToString("N"));Directory.CreateDirectory(directory);
        var refs=references.Select((p,i)=>{string target=Path.Combine(directory,"reference-"+i+Path.GetExtension(p));File.Copy(p,target);return target;}).ToArray();
        var library=MaterialService.Library;var catalog=library.List();var plantLibrary=PlantService.Library;var plantCatalog=plantLibrary.List();
        var job=new MaterialChatJob();jobs.Add(job.Id,job);var cancel=new CancellationTokenSource();workers.Add(job.Id,cancel);
        _=Task.Run(async()=>
        {
            try
            {
                Ui(()=>job.Stage="正在判断素材任务…");
                var intent=await CodexPlantAgent.RunAsync(Path.Combine(directory,"intent"),"route",conversation,[],refs,cancel.Token);
                if(intent.Plant)
                {
                    Ui(()=>job.Kind="plant");
                    await PlantChat.Process(job,plantLibrary,plantCatalog,directory,conversation,refs,reuseSimilar,intent.Generate,cancel.Token,action=>Ui(()=>{try{action();}catch(Exception e){job.Status=e is OperationCanceledException?"cancelled":"failed";job.Error=e.Message;job.Stage=e.Message;Release(job.Id);}}));
                    Ui(()=>Release(job.Id));return;
                }
                if(reuseSimilar&&catalog.Length>0)
                {
                    Ui(()=>job.Stage="正在查找可复用的已有材质…");
                    var found=await CodexCatalogRunner.RunAsync(Path.Combine(directory,"search"),"search",conversation,catalog,cancel.Token,refs);
                    cancel.Token.ThrowIfCancellationRequested();
                    if(found.MaterialRequest&&found.Matches.Length>0)
                    {
                        Ui(()=>{try{cancel.Token.ThrowIfCancellationRequested();job.Matches=found.Matches;job.Reply="找到相近材质，可在下方候选中选择后应用：\n"+string.Join("\n",found.Matches.Select(m=>catalog.First(a=>a.Id==m.Id).Name+" · "+m.Reason))+"\n需要全新方案时，关闭‘优先复用’后再次发送。";job.Status="completed";job.Stage="找到可复用材质，等待选择。";}catch(OperationCanceledException){job.Status="cancelled";job.Stage="已取消";}finally{Release(job.Id);}});return;
                    }
                }
                var result=await CodexMaterialChatRunner.RunAsync(directory,$"Physical tile size: {widthMeters:G8} x {heightMeters:G8} meters.\n"+conversation,refs,stage=>Ui(()=>job.Stage=stage),cancel.Token);
                CatalogLabel? label=null;
                string? labelError=null;
                if(result.ImagePath!=null)
                {
                    Ui(()=>job.Stage="正在归入分类并生成标签…");
                    try{label=await CatalogService.LabelAsync(library,asset,Path.Combine(directory,"label"),cancel.Token,result.ImagePath);}
                    catch(Exception e) when(e is not OperationCanceledException){labelError=e.Message;asset.Category="待分类";asset.Tags=["待整理"];}
                }
                Ui(()=>
                {
                    try
                    {
                        cancel.Token.ThrowIfCancellationRequested();if(MaterialService.Library.Root!=library.Root)throw new InvalidOperationException("材质库已切换。");if(label!=null)CatalogService.SetLabel(asset,label);job.Reply=result.Reply;
                        if(result.ImagePath!=null){var imported=MaterialService.Import(asset,new(){{"baseColor",result.ImagePath}});job.Material=imported.Id;job.ImagePath=MaterialService.Library.MapPath(imported,"baseColor");}
                        if(labelError!=null)job.Reply+="\n图片已保存，但自动分类未完成，可用材质库的 AI 整理重试。";
                        job.Status="completed";job.Stage=job.Material.HasValue?(labelError==null?"新材质已生成并入库":"图片已入库，自动分类失败，可重试整理"):"回复完成";
                    }
                    catch(OperationCanceledException){job.Status="cancelled";job.Stage="已取消";}
                    catch(Exception e){job.Status="failed";job.Error=e.Message;job.Stage=e.Message;}
                    finally{Release(job.Id);}
                });
            }
            catch(Exception e){Ui(()=>{job.Status=e is OperationCanceledException?"cancelled":"failed";job.Stage=e is OperationCanceledException?"已取消":e.Message;job.Error=e.Message;Release(job.Id);});}
        });return job;
    }
    private static void Release(Guid id){if(workers.Remove(id,out var cancel))cancel.Dispose();}
}

/// <summary>Authenticated loopback UI transport for the official ChatKit SDK, not an MCP server.</summary>
internal sealed class MaterialChatHost : IDisposable
{
    private static readonly string session=Environment.ProcessId+"-"+Guid.NewGuid().ToString("N");
    private readonly uint document;
    private Process? process;
    private readonly SemaphoreSlim writer=new(1);
    private readonly Func<(double Width,double Height)> size;
    private readonly Action<Guid> onStarted;
    private readonly Func<bool> reuse;
    private bool disposed;
    private Guid? active;
    private readonly string data;
    internal string Url{get;private set;}="";
    internal string State{get;private set;}="尚未启动";
    internal MaterialChatHost(uint doc,Func<(double,double)> size,Action<Guid> onStarted,Func<bool>? reuse=null)
    {
        document=doc;this.size=size;this.onStarted=onStarted;this.reuse=reuse??(()=>true);
        data=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"RhinoSceneFlow","chatkit-data","sessions",session,"doc-"+doc,Guid.NewGuid().ToString("N"));Directory.CreateDirectory(data);
    }
    internal async Task StartAsync()
    {
        if(disposed)throw new OperationCanceledException();
        string python=Environment.GetEnvironmentVariable("RHINOSCENEFLOW_CHATKIT_PYTHON")??Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"RhinoSceneFlow","chatkit-runtime","Scripts","python.exe");
        if(!File.Exists(python))throw new InvalidOperationException("请先运行 scripts/Setup-ChatKit.ps1 安装本机 ChatKit 运行环境。");
        var listener=new TcpListener(IPAddress.Loopback,0);listener.Start();int port=((IPEndPoint)listener.LocalEndpoint).Port;listener.Stop();
        string token=Convert.ToHexString(System.Security.Cryptography.RandomNumberGenerator.GetBytes(32));
        var info=new ProcessStartInfo(python){UseShellExecute=false,CreateNoWindow=true,RedirectStandardInput=true,RedirectStandardOutput=true,RedirectStandardError=true,StandardOutputEncoding=System.Text.Encoding.UTF8,StandardInputEncoding=new System.Text.UTF8Encoding(false)};
        info.ArgumentList.Add(Path.Combine(Path.GetDirectoryName(typeof(MaterialChatHost).Assembly.Location)!,"ChatKit","server.py"));info.ArgumentList.Add("--port");info.ArgumentList.Add(port.ToString());info.ArgumentList.Add("--data");info.ArgumentList.Add(data);info.Environment["SCENEFLOW_CHAT_TOKEN"]=token;info.Environment["PYTHONUTF8"]="1";
        process=new Process{StartInfo=info};process.Start();_=ReadAsync(process);_=LogAsync(process);
        using var http=new System.Net.Http.HttpClient{Timeout=TimeSpan.FromSeconds(1)};
        for(int i=0;i<100;i++)
        {
            if(disposed)throw new OperationCanceledException();if(process.HasExited)throw new InvalidOperationException("ChatKit 后端启动失败，请查看 chatkit-data/server.log。");
            try{using var response=await http.GetAsync($"http://127.0.0.1:{port}/health");if(response.IsSuccessStatusCode){Url=$"http://127.0.0.1:{port}/?token={token}";State="ready";return;}}catch(System.Net.Http.HttpRequestException){}catch(TaskCanceledException){}
            await Task.Delay(100);
        }throw new TimeoutException("ChatKit 后端启动超时。");
    }
    private async Task LogAsync(Process child)
    {try{using var log=new StreamWriter(Path.Combine(data,"server.log"),false);while(await child.StandardError.ReadLineAsync() is {} line){await log.WriteLineAsync(line);await log.FlushAsync();}}catch(IOException){}catch(ObjectDisposedException){}}
    private async Task ReadAsync(Process child)
    {
        try
        {
            while(await child.StandardOutput.ReadLineAsync() is {} line)
            {
                using var json=JsonDocument.Parse(line);var request=json.RootElement.Clone();
                RhinoApp.InvokeOnUiThread(new Action(()=>
                {
                    object response;
                    try
                    {
                        if(disposed)throw new OperationCanceledException();var p=request.GetProperty("params");object result;
                        switch(request.GetProperty("method").GetString())
                        {
                            case "turn.start":
                                var doc=RhinoDoc.FromRuntimeSerialNumber(document);if(doc==null||!doc.IsAvailable||doc.IsClosing||RhinoDoc.ActiveDoc?.RuntimeSerialNumber!=document)throw new InvalidOperationException("请切换到此对话对应的文档后再发送。");
                                var refs=p.GetProperty("references").EnumerateArray().Select(v=>Path.GetFullPath(v.GetString()!)).ToArray();
                                if(refs.Any(path=>!path.StartsWith(Path.GetFullPath(data)+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase)))throw new ArgumentException("参考图必须来自本次聊天上传。");
                                var dimensions=size();var job=MaterialChat.Start(p.GetProperty("conversation").GetString()!,refs,dimensions.Width,dimensions.Height,reuse());active=job.Id;onStarted(job.Id);result=job;break;
                            case "turn.status":result=MaterialChat.Get(Guid.Parse(p.GetProperty("jobId").GetString()!));break;
                            case "turn.cancel":result=MaterialChat.Cancel(Guid.Parse(p.GetProperty("jobId").GetString()!));break;
                            default:throw new ArgumentException("未知聊天请求。");
                        }
                        response=new{id=request.GetProperty("id").GetString(),result};
                    }
                    catch(Exception e){response=new{id=request.GetProperty("id").GetString(),error=e.Message};}
                    _=ReplyAsync(child,response);
                }));
            }
        }catch(Exception e) when(e is IOException or ObjectDisposedException or InvalidOperationException){State=e.Message;}
    }
    private async Task ReplyAsync(Process child,object response)
    {
        await writer.WaitAsync();try{if(!disposed){await child.StandardInput.WriteLineAsync(JsonSerializer.Serialize(response,new JsonSerializerOptions{PropertyNamingPolicy=JsonNamingPolicy.CamelCase}));await child.StandardInput.FlushAsync();}}catch(IOException){}catch(InvalidOperationException){}finally{writer.Release();}
    }
    public void Dispose()
    {
        if(disposed)return;disposed=true;if(active.HasValue&&MaterialChat.Get(active.Value).Status=="running")MaterialChat.Cancel(active.Value);
        try{if(process!=null&&!process.HasExited)process.Kill(true);}catch(InvalidOperationException){}catch(System.ComponentModel.Win32Exception){}
        // Reader tasks retain the Process until streams reach EOF.
    }
}

internal sealed class MaterialChatView : Panel,IDisposable
{
    internal readonly Microsoft.Web.WebView2.Wpf.WebView2 Browser=new();
    private readonly MaterialChatHost host;
    private readonly Label error=new(){Wrap=WrapMode.Word};
    private bool closed,started,stopped;
    internal string State{get;private set;}="尚未启动";
    internal MaterialChatView(uint doc,Func<(double,double)> size,Action<Guid> startedJob,Func<bool>? reuse=null)
    {
        host=new(doc,size,startedJob,reuse);Content=new NativeControlHost(Browser);
    }
    internal async Task StartAsync()
    {
        if(started||closed||stopped)return;started=true;
        try
        {
            await host.StartAsync();if(closed||stopped)return;
            string userData=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"RhinoSceneFlow","webview");
            var env=await CoreWebView2Environment.CreateAsync(null,userData);if(closed||stopped)return;
            await Browser.EnsureCoreWebView2Async(env);if(closed||stopped)return;
            Browser.CoreWebView2.NewWindowRequested+=(_,e)=>e.Handled=true;
            Browser.CoreWebView2.NavigationStarting+=(_,e)=>{if(!e.Uri.StartsWith(host.Url.Split('?')[0],StringComparison.Ordinal)&&e.Uri!="about:blank")e.Cancel=true;};
            Browser.CoreWebView2.Settings.AreDevToolsEnabled=false;Browser.CoreWebView2.Settings.AreDefaultContextMenusEnabled=false;
            Browser.Source=new Uri(host.Url);State="ready";
        }
        catch(Exception e){if(!closed&&!stopped){State=e.Message;error.Text="ChatKit 无法启动："+e.Message+"\n请检查本机 ChatKit 运行环境与网络连接。";Content=error;host.Dispose();}}
    }
    internal void Stop(){stopped=true;host.Dispose();}
    protected override void Dispose(bool disposing)
    {
        if(disposing)
        {
            if(closed)return;closed=true;host.Dispose();var content=Content;Content=null;
            content?.Dispose();Browser.Dispose();
        }
        base.Dispose(disposing);
    }
}
