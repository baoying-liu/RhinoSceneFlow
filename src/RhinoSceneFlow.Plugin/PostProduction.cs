using System.Collections.Concurrent;
using System.Diagnostics;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Eto.Forms;
using Rhino;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class PostProductionJob
{
    public Guid Id {get;}=Guid.NewGuid();
    public string Status {get;internal set;}="running";
    public string Stage {get;internal set;}="正在启动本机工作台";
    public string? Url {get;internal set;}
    public string? Project {get;internal set;}
    public string? ImportJob {get;internal set;}
    public string? Error {get;internal set;}
    public JsonElement? Response {get;internal set;}
}

/// <summary>Owned file snapshots only cross this boundary. No RhinoDoc access on workers.</summary>
public static class PostProduction
{
    private static readonly string ServiceVersion=typeof(PostProduction).Assembly.GetName().Version!.ToString(3);
    private static readonly ConcurrentDictionary<Guid,PostProductionJob> jobs=new();
    private static readonly SemaphoreSlim launch=new(1);
    private static readonly string root=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"RhinoSceneFlow","postproduction");
    private static readonly JsonSerializerOptions json=new(){PropertyNamingPolicy=JsonNamingPolicy.CamelCase};
    public static PostProductionJob Get(Guid id)=>jobs.TryGetValue(id,out var job)?job:throw new ArgumentException("后期启动任务不存在。");
    public static PostProductionJob Request(string route,string method,string? body=null)
    {
        if(!System.Text.RegularExpressions.Regex.IsMatch(route,@"^/api/(status|projects|jobs|boards|board-preferences)(/[A-Za-z0-9_-]+)*$")||route.Contains("..",StringComparison.Ordinal))throw new ArgumentException("需要工作台 status、projects、jobs、boards 或 board-preferences 的相对 JSON 路由。");
        if(method is not ("GET" or "POST" or "PUT"))throw new ArgumentException("method: GET | POST | PUT");
        var job=new PostProductionJob{Stage="正在连接后期工作台"};jobs[job.Id]=job;string? codex=CodexImageRunner.FindExecutable();
        _=Task.Run(async()=>
        {
            try
            {
                var service=await EnsureAsync(codex);using var http=Client(service.Token);
                using var request=new HttpRequestMessage(new HttpMethod(method),$"http://127.0.0.1:{service.Port}"+route);
                if(body!=null)request.Content=new StringContent(body,Encoding.UTF8,"application/json");
                using var response=await http.SendAsync(request,HttpCompletionOption.ResponseHeadersRead);
                if(response.Content.Headers.ContentType?.MediaType!="application/json")throw new InvalidOperationException("该路由返回文件，请在 Web 工作台下载。");
                using var value=JsonDocument.Parse(await response.Content.ReadAsStringAsync());
                if(!response.IsSuccessStatusCode)throw new InvalidOperationException(value.RootElement.TryGetProperty("detail",out var detail)?detail.ToString():"后期请求失败。");
                job.Response=value.RootElement.Clone();job.Stage="工作台请求已完成";job.Status="completed";
            }
            catch(Exception e){job.Error=e.Message;job.Stage=e.Message;job.Status="failed";}
        });return job;
    }
    public static PostProductionJob Start(RhinoDoc doc,string? path=null,bool browser=false)
    {
        NamedViewExportService.RequireActive(doc);
        if(path!=null&&(!Path.IsPathFullyQualified(path)||!File.Exists(path)||Path.GetExtension(path).ToLowerInvariant() is not (".psd" or ".psb")))throw new ArgumentException("请选择现有 PSD / PSB 的绝对路径。");
        // Capture on Rhino's UI thread; this context describes the CURRENT document,
        // not a claim that its camera/settings match an older imported PSD.
        string context=JsonSerializer.Serialize(new{document=doc.RuntimeSerialNumber,documentPath=doc.Path,documentName=doc.Name,
            activeView=doc.Views.ActiveView?.ActiveViewport.Name,source="Rhino current-document context",capturedUtc=DateTime.UtcNow},json);
        string? codex=CodexImageRunner.FindExecutable();
        var job=new PostProductionJob();jobs[job.Id]=job;
        _=Task.Run(async()=>
        {
            try
            {
                var service=await EnsureAsync(codex);string url=$"http://127.0.0.1:{service.Port}";
                if(path!=null)
                {
                    job.Stage="正在把 PSD 快照交给工作台";
                    using var http=Client(service.Token);using var response=await http.PostAsync(url+"/api/import",new StringContent("{\"path\":"+JsonSerializer.Serialize(path)+",\"context\":"+context+"}",Encoding.UTF8,"application/json"));
                    using var result=JsonDocument.Parse(await response.Content.ReadAsStringAsync());
                    if(!response.IsSuccessStatusCode)throw new InvalidOperationException(result.RootElement.GetProperty("detail").ToString());
                    job.Project=result.RootElement.GetProperty("project").GetString();job.ImportJob=result.RootElement.GetProperty("job").GetString();
                }
                job.Url=url+"/#token="+Uri.EscapeDataString(service.Token)+(job.Project!=null?"&project="+job.Project:"");
                if(browser)Process.Start(new ProcessStartInfo(job.Url){UseShellExecute=true});
                job.Stage=path==null?"工作台已启动":"PSD 已提交，工作台正在解析图层";job.Status="completed";
            }
            catch(Exception e){job.Error=e.Message;job.Stage=e.Message;job.Status="failed";}
        });return job;
    }
    private sealed record Service(int Port,string Token);
    private static HttpClient Client(string token){var client=new HttpClient{Timeout=TimeSpan.FromSeconds(120)};client.DefaultRequestHeaders.Authorization=new AuthenticationHeaderValue("Bearer",token);return client;}
    private static async Task<Service?> ExistingAsync()
    {
        try
        {
            using var record=JsonDocument.Parse(await File.ReadAllTextAsync(Path.Combine(root,"service.json")));var r=record.RootElement;
            int port=r.GetProperty("port").GetInt32();if(port is <1 or >65535)return null;
            string token=r.GetProperty("token").GetString()!;using var http=Client(token);http.Timeout=TimeSpan.FromSeconds(1);
            using var response=await http.GetAsync($"http://127.0.0.1:{port}/api/status");if(!response.IsSuccessStatusCode)return null;
            using var state=JsonDocument.Parse(await response.Content.ReadAsStringAsync());
            if(state.RootElement.GetProperty("service").GetString()!="RhinoSceneFlow.PostProduction")return null;
            if(state.RootElement.GetProperty("version").GetString()!=ServiceVersion)throw new NotSupportedException("后期工作台有旧版服务正在运行，请在旧页面点击‘关闭服务’再打开新版。");
            return new(port,token);
        }
        catch(Exception e) when(e is IOException or JsonException or HttpRequestException or TaskCanceledException){return null;}
    }
    private static async Task<Service> EnsureAsync(string? codex)
    {
        await launch.WaitAsync();
        try
        {
            if(await ExistingAsync() is {} existing)return existing;
            string python=Environment.GetEnvironmentVariable("RHINOSCENEFLOW_CHATKIT_PYTHON")??Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"RhinoSceneFlow","chatkit-runtime","Scripts","python.exe");
            if(!File.Exists(python))throw new InvalidOperationException("请先运行 scripts/Setup-PostProduction.ps1 安装后期运行环境。");
            string script=Path.Combine(Path.GetDirectoryName(typeof(PostProduction).Assembly.Location)!,"PostProduction","server.py");
            Directory.CreateDirectory(root);var info=new ProcessStartInfo(python){UseShellExecute=false,CreateNoWindow=true,WindowStyle=ProcessWindowStyle.Hidden};
            foreach(string arg in new[]{"-I","-X","utf8",script,"--data",root})info.ArgumentList.Add(arg);
            if(codex!=null){info.ArgumentList.Add("--codex");info.ArgumentList.Add(codex);}
            // The service owns itself and persisted projects. Closing a panel/document never kills it.
            using var child=Process.Start(info)??throw new InvalidOperationException("后期服务未能启动。");
            for(int i=0;i<120;i++)
            {
                if(await ExistingAsync() is {} ready)return ready;
                if(child.HasExited&&child.ExitCode!=0)throw new InvalidOperationException("后期服务启动失败，请运行 scripts/Setup-PostProduction.ps1 检查依赖。");
                await Task.Delay(150);
            }
            throw new TimeoutException("后期服务启动超时，请检查运行环境后重试。");
        }
        finally{launch.Release();}
    }
}

internal sealed class PostProductionTool:Panel
{
    private readonly RhinoDoc doc;
    private readonly Label status=new(){Wrap=WrapMode.Word};
    private readonly DropDown files=new();
    private readonly UITimer timer=new(){Interval=.4};
    private Guid? active;
    internal PostProductionTool(RhinoDoc doc)
    {
        this.doc=doc;var layout=Ui.Layout();layout.AddRow(ToolUi.Heading("AI 后期 · Web 工作台"));
        layout.AddRow(new Label{Text="在列表与画布之间切换：先整图探索、标注修改，再高清细化。图片、版本与工程自动保存在本机，显示语言可在网页设置中调整。",Wrap=WrapMode.Word});
        layout.AddRow(Ui.Button("打开 Web 工作台",()=>Start(null)));
        layout.AddRow(new Label{Text="当前导出文件夹中的 PSD"});layout.AddRow(files);
        layout.AddRow(Ui.Button("刷新文件列表",Refresh),Ui.Button("发送所选 PSD",()=>{if(files.SelectedKey is {} path)Start(path);else status.Text="请先选择一个 PSD。";}));
        layout.AddRow(Ui.Button("选择其他 PSD…",()=>{using var dialog=new OpenFileDialog();dialog.Filters.Add(new FileFilter("Photoshop 文件",".psd",".psb"));if(dialog.ShowDialog(this)==DialogResult.Ok)Start(dialog.FileName);}));
        layout.AddRow(status);layout.AddRow(new Label{Text="在网页中先测试分块，再批量生成并融合为完整 PNG。失败图块可以继续处理。",Wrap=WrapMode.Word});layout.Add(null,true,true);Content=layout;
        timer.Elapsed+=(_,_)=>{if(active is {} id){var job=PostProduction.Get(id);status.Text=job.Stage;if(job.Status!="running"){active=null;timer.Stop();}}};Refresh();
    }
    internal void Start(string? path){try{var job=PostProduction.Start(doc,path,true);active=job.Id;status.Text=job.Stage;timer.Start();}catch(Exception e){status.Text=e.Message;}}
    private void Refresh()
    {
        files.Items.Clear();string directory=SceneFlowPlugin.Instance.ExportDirectory;
        try{if(Directory.Exists(directory))foreach(var path in Directory.EnumerateFiles(directory,"*.psd").OrderByDescending(File.GetLastWriteTimeUtc).Take(50))files.Items.Add(new ListItem{Key=path,Text=Path.GetFileName(path)});if(files.Items.Count>0)files.SelectedIndex=0;status.Text=directory;}
        catch(IOException e){status.Text=e.Message;}
    }
    public object State()=>new{document=doc.RuntimeSerialNumber,activeJob=active,stage=status.Text};
    protected override void Dispose(bool disposing){if(disposing){timer.Stop();timer.Dispose();}base.Dispose(disposing);}
}

public sealed class PostProductionCommand:Rhino.Commands.Command
{
    public override string EnglishName=>"RhinoSceneFlowPostProduction";
    protected override Rhino.Commands.Result RunCommand(RhinoDoc doc,Rhino.Commands.RunMode mode)
    {SceneFlowWorkspace.Open("post");if(SceneFlowWorkspace.Hosts.GetValueOrDefault("post")?.Tool is PostProductionTool tool)tool.Start(null);return Rhino.Commands.Result.Success;}
}
