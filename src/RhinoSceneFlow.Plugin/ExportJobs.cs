using System.Security.Cryptography;
using System.Text.Json;
using Rhino;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

/// <summary>Durable receipts shared by the panel and original-Platform automation.</summary>
public static class ExportJobs
{
    private sealed record Target(Guid ViewId,string Name,string Path,int Width,int Height);
    private sealed class Job
    {
        internal Guid Id;internal uint Document;internal string Key="",Status="queued",Stage="queued",Current="";internal int Total;
        internal readonly List<BatchFileResult> Files=[];internal readonly CancellationTokenSource Cancel=new();
        internal bool Terminal;internal string? Error;internal DateTime Updated=DateTime.UtcNow;
        internal Target[] Targets=[];
    }
    private static readonly object gate=new();
    private static readonly Dictionary<Guid,Job> jobs=[];
    private static string Root=>Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"RhinoSceneFlow",InstallationContext.Sandbox?"sandbox-export-jobs":"production/export-jobs");
    private static string FileFor(Guid id)=>Path.Combine(Root,id.ToString("N")+".json");
    private static object Snapshot(Job j)=>new{jobId=j.Id,document=j.Document,status=j.Status,stage=j.Stage,currentView=j.Current,total=j.Total,finished=j.Files.Count,targets=j.Targets,files=j.Files.ToArray(),terminal=j.Terminal,error=j.Error,cancelRequested=j.Cancel.IsCancellationRequested,updated=j.Updated,receipt=FileFor(j.Id),report=new BatchReport(j.Files.ToArray(),j.Status=="cancelled")};
    private static void Save(Job j)
    {
        j.Updated=DateTime.UtcNow;Directory.CreateDirectory(Root);
        var path=FileFor(j.Id);var tmp=path+"."+Guid.NewGuid().ToString("N")+".tmp";
        try{File.WriteAllText(tmp,JsonSerializer.Serialize(Snapshot(j),MaterialLibrary.Json));File.Move(tmp,path,true);}
        finally{if(File.Exists(tmp))File.Delete(tmp);}
    }
    public static object State(Guid id)
    {
        lock(gate)
        {
            if(jobs.TryGetValue(id,out var j))return Snapshot(j);
            if(!File.Exists(FileFor(id)))throw new ArgumentException("Export job not found.");
            var value=System.Text.Json.Nodes.JsonNode.Parse(File.ReadAllText(FileFor(id)))!;
            if(value["terminal"]?.GetValue<bool>()!=true){value["status"]="interrupted";value["stage"]="interrupted";value["terminal"]=true;value["error"]="The host stopped before a final receipt was recorded. Inspect recorded output paths before starting a new job.";}
            return value;
        }
    }
    public static object Cancel(Guid id)
    {
        lock(gate){if(jobs.TryGetValue(id,out var j)&&!j.Terminal&&!j.Cancel.IsCancellationRequested){j.Cancel.Cancel();Save(j);}return State(id);}
    }
    public static object List(uint document)
    {
        lock(gate)return new{jobs=jobs.Values.Where(j=>j.Document==document).OrderByDescending(j=>j.Updated).Select(Snapshot).ToArray()};
    }
    public static Guid Start(RhinoDoc doc,Func<WorkbenchPlan[]> makePlan,Guid id,string requestKey)
    {
        NamedViewExportService.RequireActive(doc);PlantEditing.RequireFinished(doc);
        string key=Convert.ToHexString(SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(requestKey)));
        lock(gate)
        {
            if(id==Guid.Empty)throw new ArgumentException("A non-empty requestId is required.");
            if(jobs.TryGetValue(id,out var prior)){if(prior.Document!=doc.RuntimeSerialNumber||prior.Key!=key)throw new ArgumentException("requestId already belongs to another export request.");return id;}
            if(File.Exists(FileFor(id)))throw new InvalidOperationException("This requestId has a saved receipt from a previous host. Query export_job_status; do not resubmit it.");
            if(jobs.Values.Any(j=>!j.Terminal))throw new InvalidOperationException("An export is already running. Wait for completion or cancel it.");
            var plan=makePlan().Select(p=>p with{View=JsonSerializer.Deserialize<ViewExportRow>(JsonSerializer.Serialize(p.View,MaterialLibrary.Json),MaterialLibrary.Json)!}).ToArray();
            if(plan.Length==0)throw new ArgumentException("No views selected for export.");
            var job=new Job{Id=id,Document=doc.RuntimeSerialNumber,Key=key,Total=plan.Length,Targets=plan.Select(p=>new Target(p.View.Id,p.View.Name,p.Path,p.View.Width,p.View.Height)).ToArray()};Save(job);jobs.Add(id,job);
            // Defer beyond the RPC response. Workers never traverse a Rhino document.
            Eto.Forms.Application.Instance.AsyncInvoke(()=>{_ = Run(job,plan);});
            return id;
        }
    }
    private static Task<T> OnUi<T>(Func<T> callback)
    {
        var completion=new TaskCompletionSource<T>(TaskCreationOptions.RunContinuationsAsynchronously);
        RhinoApp.InvokeOnUiThread(new Action(()=>{try{completion.SetResult(callback());}catch(Exception e){completion.SetException(e);}}));return completion.Task;
    }
    private static async Task Run(Job job,WorkbenchPlan[] plan)
    {
        var token=job.Cancel.Token;
        try
        {
            foreach(var item in plan)
            {
                token.ThrowIfCancellationRequested();
                lock(gate){job.Status="running";job.Stage="capturing";job.Current=item.View.Name;Save(job);}
                BatchFileResult result;
                try
                {
                    var prepared=await OnUi(()=>{token.ThrowIfCancellationRequested();var doc=RhinoDoc.FromRuntimeSerialNumber(job.Document);if(doc==null||!doc.IsAvailable||doc.IsClosing||doc.IsOpening)throw new OperationCanceledException(token);NamedViewExportService.RequireActive(doc);return WorkbenchService.Prepare(doc,item,token);});
                    try{lock(gate){job.Stage="writing";Save(job);}result=await Task.Run(()=>prepared.Write(token),token);}
                    finally{await OnUi(()=>{prepared.Dispose();return true;});}
                }
                catch(OperationCanceledException){throw;}
                catch(Exception e){result=new(item.View.Id,item.View.Name,item.Path,false,item.View.Width,item.View.Height,0,0,e.Message);}
                lock(gate){job.Files.Add(result);Save(job);}
            }
            lock(gate){job.Status=job.Files.All(f=>f.Ok)?"completed":job.Files.Any(f=>f.Ok)?"partial":"failed";}
        }
        catch(OperationCanceledException){lock(gate){job.Status="cancelled";}}
        catch(Exception e){lock(gate){job.Status="failed";job.Error=e.Message;}}
        finally{lock(gate){job.Terminal=true;job.Stage=job.Status;try{Save(job);}catch(Exception e){job.Error="Unable to save final receipt: "+e.Message;}}}
    }
}
