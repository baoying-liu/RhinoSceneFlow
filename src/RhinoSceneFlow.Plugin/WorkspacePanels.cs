using System.Runtime.InteropServices;
using System.Reflection;
using Eto.Drawing;
using Eto.Forms;
using Rhino;
using Rhino.UI;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public static class SceneFlowWorkspace
{
    private static readonly Type[] pages=[typeof(MaterialToolPanel),typeof(MaterialLibraryToolPanel),typeof(UvToolPanel),typeof(PlantToolPanel),typeof(ExportToolPanel),typeof(PlantsListToolPanel),typeof(PropertiesToolPanel),typeof(PostProductionToolPanel)];
    private static readonly Dictionary<uint,Guid> selectedAssets=[];
    private static readonly Dictionary<uint,string> materialScopes=[];
    internal static readonly Dictionary<string,WorkspaceHost> Hosts=[];
    internal static readonly HashSet<WorkspaceHost> AllHosts=[];
    private static bool opening;
    internal static void Register(SceneFlowPlugin plugin)
    {
        string[] titles=["SceneFlow · AI 素材","SceneFlow · 材质库","SceneFlow · UV","SceneFlow · 种植","SceneFlow · PSD","SceneFlow · Plants List","SceneFlow · 属性","SceneFlow · AI 后期"];
        string[] icons=["Materials","Library","Uv","Planting","Export","Planting","Uv","Export"];
        for(int i=0;i<pages.Length;i++)Panels.RegisterPanel(plugin,pages[i],titles[i],typeof(SceneFlowPlugin).Assembly,"RhinoSceneFlow.Plugin.Resources."+icons[i]+".ico",PanelType.System);
        RhinoDoc.CloseDocument+=OnDocumentClosed;
    }
    private static void OnDocumentClosed(object? sender,DocumentEventArgs e){uint serial=e.Document.RuntimeSerialNumber;selectedAssets.Remove(serial);materialScopes.Remove(serial);UnwrapService.CancelDocument(serial);RandomTextureService.CancelDocument(serial);}
    public static object Open(string page="materials")
    {
        var type=page switch{"materials"=>pages[0],"library"=>pages[1],"uv"=>pages[2],"planting"=>pages[3],"export"=>pages[4],"plantsList"=>pages[5],"properties"=>pages[6],"post"=>pages[7],_=>throw new ArgumentException("page: materials | library | uv | planting | export | plantsList | properties | post")};
        if(opening)return State();opening=true;
        try
        {
            bool seed=!SceneFlowPlugin.Instance.Settings.GetBool("WorkspaceSeeded013",false)&&pages.All(t=>Panels.PanelDockBars(t.GUID).Length==0);
            if(Panels.PanelDockBars(type.GUID).Length==0)
            {
                var group=pages.Where(p=>p!=type).SelectMany(p=>Panels.PanelDockBars(p.GUID)).FirstOrDefault();
                if(group!=Guid.Empty)Panels.OpenPanel(group,type.GUID,true);else Panels.OpenPanel(type,true);
            }
            else Panels.OpenPanel(type,true);
            if(seed){var bars=Panels.PanelDockBars(type.GUID);if(bars.Length>0){foreach(var p in pages)if(p!=type)Panels.OpenPanel(bars[0],p.GUID,false);SceneFlowPlugin.Instance.Settings.SetBool("WorkspaceSeeded013",true);}}
            Panels.OpenPanel(type,true);if(Hosts.TryGetValue(page,out var host))host.RefreshDocument();EnsureReadableFloatingSize(type);return State();
        }
        finally{opening=false;}
    }
    public static object Group()
    {
        Open();var bars=Panels.PanelDockBars(pages[0].GUID);if(bars.Length==0)throw new InvalidOperationException("Workspace container unavailable.");
        foreach(var p in pages)Panels.OpenPanel(bars[0],p.GUID,p==pages[0]);Panels.OpenPanel(pages[0],true);EnsureReadableFloatingSize(pages[0]);return State();
    }
    // Rhino 8's modern floating container has a 200x200 default and ignores the
    // hosted Eto panel's preferred size. Match RhinoBIM V2's isolated compatibility
    // boundary; never float, move or resize an existing usable/docked container.
    private static void EnsureReadableFloatingSize(Type page)
    {
        const BindingFlags flags=BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static|BindingFlags.Instance;
        var assembly=AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a=>a.GetName().Name=="Rhino.UI");
        var registry=assembly?.GetType("Rhino.UI.Internal.TabPanels.TabPanelDockBars");var find=registry?.GetMethod("FromDockBarId",flags,null,[typeof(Guid)],null);
        if(find==null)return;
        foreach(var id in Panels.PanelDockBars(page.GUID))
        {
            var bar=find.Invoke(null,[id]);var form=bar?.GetType().GetMethod("HasFloatingForm",flags,null,[typeof(uint)],null)?.Invoke(bar,[RhinoDoc.ActiveDoc?.RuntimeSerialNumber??0]) as Form;
            if(form is not null&&(form.ClientSize.Width<320||form.ClientSize.Height<450))form.ClientSize=new(400,800);
        }
    }
    public static object State()=>new{pages=pages.Select(t=>new{panelId=t.GUID,open=Panels.IsPanelVisible(t,false),selected=Panels.IsPanelVisible(t,true),dockBars=Panels.PanelDockBars(t.GUID)}).ToArray(),tools=Hosts.ToDictionary(p=>p.Key,p=>p.Value.State())};
    internal static MaterialsTool? Materials=>Hosts.GetValueOrDefault("materials")?.Tool as MaterialsTool;
    internal static MaterialsTool? Library=>Hosts.GetValueOrDefault("library")?.Tool as MaterialsTool;
    internal static IEnumerable<MaterialsTool> MaterialTools(uint document)=>AllHosts.Select(h=>h.Tool).OfType<MaterialsTool>().Where(t=>t.DocumentSerial==document);
    internal static Guid? SelectedAsset(uint document)=>selectedAssets.TryGetValue(document,out var id)?id:null;
    internal static string MaterialScope(uint document)=>materialScopes.GetValueOrDefault(document,"object");
    internal static void SelectAsset(uint document,Guid id){MaterialService.Library.Get(id);selectedAssets[document]=id;foreach(var tool in MaterialTools(document).ToArray())tool.ReceiveAsset(id);}
    internal static void SetMaterialScope(uint document,string scope){materialScopes[document]=scope;foreach(var tool in MaterialTools(document).ToArray())tool.ReceiveScope(scope);}
    internal static bool OtherMaterialBusy(uint document,MaterialsTool current)=>MaterialTools(document).Any(t=>t!=current&&t.LocalBusy);
    internal static void MaterialProgress(uint document,string message,int percent){foreach(var tool in MaterialTools(document).ToArray())tool.ReceiveProgress(message,percent);}
    internal static ExportPanel? Export=>Hosts.GetValueOrDefault("export")?.Tool as ExportPanel;
    internal static PlantTool? Planting=>Hosts.GetValueOrDefault("planting")?.Tool as PlantTool;
    internal static void Stop()
    {
        RhinoDoc.CloseDocument-=OnDocumentClosed;
        // Registered panel controls belong to Rhino. Disposing them here leaves a
        // disposed descendant in Rhino's later UnLoad/DataContext traversal.
        foreach(var host in AllHosts.ToArray())host.Shutdown();Hosts.Clear();AllHosts.Clear();selectedAssets.Clear();materialScopes.Clear();
    }
}

public abstract class WorkspaceHost:Panel,IPanel
{
    private readonly string page;
    private readonly Panel body=new();
    private readonly UITimer documents=new(){Interval=.6};
    private uint serial;
    private bool stopped,rebinding;
    private string? error;
    internal Control? Tool{get;private set;}
    protected WorkspaceHost(string page)
    {
        this.page=page;SceneFlowWorkspace.Hosts[page]=this;SceneFlowWorkspace.AllHosts.Add(this);Padding=new(8);MinimumSize=new(320,300);
        var nav=new DropDown();foreach(var p in new[]{("materials","AI · 素材对话"),("library","材质库 · 浏览与应用"),("uv","UV · 真实尺寸展开"),("planting","植物库 · 种植"),("plantsList","Plants List · 组合管理"),("properties","属性 · 当前选择"),("export","PSD · 视图导出"),("post","AI 后期 · Web 工作台")})nav.Items.Add(new ListItem{Key=p.Item1,Text=p.Item2});nav.SelectedKey=page;
        nav.SelectedValueChanged+=(_,_)=>{if(nav.SelectedKey!=page){SceneFlowWorkspace.Open(nav.SelectedKey!);nav.SelectedKey=page;}};
        var menu=new Button{Text="⋯",Width=28,ToolTip="工作区布局"};var context=new ContextMenu();var group=new ButtonMenuItem{Text="将所有工具放入同一容器"};group.Click+=(_,_)=>{try{SceneFlowWorkspace.Group();}catch(Exception e){RhinoApp.WriteLine(e.Message);}};context.Items.Add(group);menu.Click+=(_,_)=>context.Show(menu);
        var navigation=new TableLayout{Spacing=new(6,0),Rows={new TableRow(new TableCell(nav,true),menu)}};
        var root=Ui.Layout();root.AddRow(navigation);root.Add(body,true,true);Content=root;
        Load+=(_,_)=>RefreshDocument();documents.Elapsed+=(_,_)=>RefreshDocument();documents.Start();
    }
    internal void RefreshDocument()
    {
        if(IsDisposed||stopped||rebinding)return;var doc=RhinoDoc.ActiveDoc;
        if(doc!=null&&(!doc.IsAvailable||doc.IsClosing||doc.IsOpening||doc.IsCreating||doc.IsInitializing))return;
        uint next=doc?.RuntimeSerialNumber??0;if(next==serial&&Tool!=null)return;
        if(Tool is ExportPanel {IsExporting:true}||Tool is MaterialsTool {Busy:true}||Tool is UvTool {Busy:true})return;
        rebinding=true;
        try
        {
            body.Content=null;var old=Tool;Tool=null;old?.Dispose();serial=next;error=null;
            Tool=doc==null?new Label{Text="打开 Rhino 模型后开始。"}:page switch{"materials"=>new MaterialsTool(doc),"library"=>new MaterialsTool(doc,true),"uv"=>new UvTool(doc),"export"=>new ExportPanel(doc),"planting"=>new PlantTool(doc),"plantsList"=>new PlantsListTool(doc),"properties"=>new PropertiesTool(doc),"post"=>new PostProductionTool(doc),_=>new Label{Text="打开工具"}};
            body.Content=Tool;
        }
        catch(Exception e){serial=next;error=e.ToString();Tool=new Label{Text="工具切换文档失败："+e.Message,Wrap=WrapMode.Word};body.Content=Tool;RhinoApp.WriteLine(error);}
        finally{rebinding=false;}
    }
    public object State()=>new{page,document=serial,error,details=Tool switch{MaterialsTool m=>m.GetState(),UvTool u=>u.GetState(),ExportPanel e=>e.GetState(),PlantTool p=>p.State(),PlantsListTool l=>l.State(),PropertiesTool p=>p.State(),PostProductionTool p=>p.State(),_=>new{placeholder=true}}};
    public void PanelShown(uint documentSerialNumber,ShowPanelReason reason){SceneFlowWorkspace.Hosts[page]=this;RefreshDocument();if(Tool is MaterialsTool m)m.Activate();}
    public void PanelHidden(uint documentSerialNumber,ShowPanelReason reason){}
    public void PanelClosing(uint documentSerialNumber,bool onCloseDocument){}
    internal void Shutdown()
    {
        if(stopped)return;stopped=true;documents.Stop();documents.Dispose();var tool=Tool;Tool=null;
        // Detach while the entire logical subtree is still alive.
        if(!body.IsDisposed)body.Content=null;tool?.Dispose();
    }
    protected override void Dispose(bool disposing){if(disposing){Shutdown();if(SceneFlowWorkspace.Hosts.GetValueOrDefault(page)==this)SceneFlowWorkspace.Hosts.Remove(page);SceneFlowWorkspace.AllHosts.Remove(this);}base.Dispose(disposing);}
}
[Guid("81CB328E-2733-4BBA-B326-1DE03D983E8A")]public sealed class MaterialToolPanel:WorkspaceHost{public MaterialToolPanel():base("materials") {}}
[Guid("83CE46CF-C14E-41EA-9860-AEB927AB7EB3")]public sealed class MaterialLibraryToolPanel:WorkspaceHost{public MaterialLibraryToolPanel():base("library") {}}
[Guid("7AF3B3D7-3243-4D82-A249-85FC9D0244B5")]public sealed class UvToolPanel:WorkspaceHost{public UvToolPanel():base("uv") {}}
[Guid("1912E513-436A-4104-9E1E-A1C7C2D8B006")]public sealed class PlantToolPanel:WorkspaceHost{public PlantToolPanel():base("planting") {}}
[Guid("D49742BA-B6FA-4321-8458-0C6D09F1DB18")]public sealed class ExportToolPanel:WorkspaceHost{public ExportToolPanel():base("export") {}}
[Guid("FB004A79-13AF-4F08-A249-302BA8A80621")]public sealed class PlantsListToolPanel:WorkspaceHost{public PlantsListToolPanel():base("plantsList") {}}
[Guid("99E5C935-4F86-4E7C-9DD8-FC9F9D30364D")]public sealed class PropertiesToolPanel:WorkspaceHost{public PropertiesToolPanel():base("properties") {}}
[Guid("86D17DD6-0F4B-48AB-BF31-3E21149D67D3")]public sealed class PostProductionToolPanel:WorkspaceHost{public PostProductionToolPanel():base("post") {}}

public sealed class PlantsListCommand:Rhino.Commands.Command
{public override string EnglishName=>"RhinoSceneFlowPlantsList";protected override Rhino.Commands.Result RunCommand(RhinoDoc doc,Rhino.Commands.RunMode mode){SceneFlowWorkspace.Open("plantsList");return Rhino.Commands.Result.Success;}}
public sealed class PropertiesCommand:Rhino.Commands.Command
{public override string EnglishName=>"RhinoSceneFlowProperties";protected override Rhino.Commands.Result RunCommand(RhinoDoc doc,Rhino.Commands.RunMode mode){SceneFlowWorkspace.Open("properties");return Rhino.Commands.Result.Success;}}

public sealed class WorkspaceCommand:Rhino.Commands.Command
{
    public override string EnglishName=>"RhinoSceneFlow";
    protected override Rhino.Commands.Result RunCommand(RhinoDoc doc,Rhino.Commands.RunMode mode){SceneFlowWorkspace.Open();return Rhino.Commands.Result.Success;}
}

internal static class ToolUi
{
    internal static TableLayout Row(params Control?[] controls)=>new(){Spacing=new(6,4),Rows={new TableRow(controls.Select(c=>new TableCell(c,c==null)).ToArray())}};
    internal static Label Heading(string text)=>new(){Text=text,Font=new Font(SystemFont.Bold,12)};
    internal static Guid[] Selection(RhinoDoc doc)=>doc.Objects.GetSelectedObjects(false,false).Select(o=>o.Id).Distinct().ToArray();
    internal static (Guid[]? Objects,Guid[]? Layers) Targets(RhinoDoc doc,bool layers)
    {
        var ids=Selection(doc);if(ids.Length==0)throw new ArgumentException("先在 Rhino 中选择需要处理的物件。");
        return layers?(null,ids.Select(id=>doc.Layers[doc.Objects.FindId(id)!.Attributes.LayerIndex].Id).Distinct().ToArray()):(ids,null);
    }
}

/// <summary>Shared nonblocking UV/apply queue. Click captures fresh targets once; workers never read live geometry.</summary>
internal sealed class MaterialActionQueue:IDisposable
{
    private readonly uint document;
    private readonly Action<string,int> progress;
    private readonly UITimer timer=new(){Interval=.08};
    private Queue<Action>? steps;
    private Guid? unwrap;
    private Guid? random;
    private Action? afterRandom;
    private Action? after;
    private bool disposed;
    internal bool Busy=>steps!=null||unwrap!=null||random!=null;
    internal MaterialActionQueue(uint document,Action<string,int> progress){this.document=document;this.progress=progress;timer.Elapsed+=(_,_)=>Tick();}
    internal void Start(Guid[]? objects,Guid[]? layers,MappingSettings settings,Guid? asset=null,bool force=false)
    {
        if(Busy)throw new InvalidOperationException("正在处理，请等待或取消。");var doc=RhinoDoc.FromRuntimeSerialNumber(document)??throw new InvalidOperationException("文档已关闭。");
        settings.Validate();var ids=MaterialService.ResolveTargets(doc,objects,layers);if(asset.HasValue)MaterialService.Library.Verify(MaterialService.Library.Get(asset.Value));
        if(asset.HasValue&&!settings.Checker&&!RandomTextureService.Ready(MaterialService.Library.Get(asset.Value),ids,layers))
        {
            random=RandomTextureService.Start(doc,asset.Value,objects,layers).Id;
            afterRandom=()=>Start(objects,layers,settings,asset,force);progress("正在准备随机贴图，完成后自动检查真实尺寸 UV…",0);timer.Start();return;
        }
        bool needsAtlas=settings.Mode=="xatlas"||ids.Any(id=>MaterialService.ReadUv(doc.Objects.FindId(id)!)?.Mode=="xatlas"&&!MaterialService.UvValid(doc,doc.Objects.FindId(id)!));
        if(needsAtlas){unwrap=UnwrapService.Start(doc,objects,layers).Id;after=asset.HasValue?()=>MaterialService.Apply(doc,asset.Value,objects,layers,new()):null;progress("正在展开复杂曲面…",0);timer.Start();return;}
        if(asset.HasValue)MaterialService.Apply(doc,asset.Value,objects,layers,settings,true);
        MaterialService.PrepareWorldUv(doc,objects,layers,settings,force,true);
        int done=0;steps=new();foreach(var id in ids)steps.Enqueue(()=>{MaterialService.PrepareWorldUv(doc,[id],null,settings,force);progress($"真实尺寸 UV · {++done}/{ids.Length}",done*90/ids.Length);});
        steps.Enqueue(()=>{if(asset.HasValue)MaterialService.Apply(doc,asset.Value,objects,layers,settings);progress(asset.HasValue?"材质已应用；真实尺寸 UV 已就绪。":"真实尺寸 UV 已就绪。",100);});timer.Start();
    }
    private void Tick()
    {
        if(disposed)return;
        try
        {
            if(random.HasValue)
            {
                var job=RandomTextureService.Get(random.Value);progress(job.Stage,job.Percent);if(job.Status=="running")return;
                random=null;var continuation=afterRandom;afterRandom=null;if(job.Status=="completed")continuation?.Invoke();
            }
            if(unwrap.HasValue){var job=UnwrapService.Get(unwrap.Value);progress(job.Stage,job.Percent);if(job.Status=="running")return;unwrap=null;var action=after;after=null;if(job.Status=="completed"){action?.Invoke();progress("展开完成"+(action==null?"。":"，材质已应用。"),100);}}
            if(steps!=null){if(steps.Count>0)steps.Dequeue()();if(steps.Count==0)steps=null;}
            if(!Busy)timer.Stop();
        }
        catch(Exception e){steps=null;unwrap=null;after=null;timer.Stop();progress(e.Message,0);}
    }
    internal void Cancel(){steps=null;after=null;afterRandom=null;if(random.HasValue)RandomTextureService.Cancel(random.Value);if(unwrap.HasValue)UnwrapService.Cancel(unwrap.Value);progress("正在停止后续步骤；已完成的修改可用 Rhino 撤销。",0);}
    public void Dispose(){if(disposed)return;disposed=true;steps=null;after=null;afterRandom=null;if(random.HasValue)RandomTextureService.Cancel(random.Value);random=null;if(unwrap.HasValue)UnwrapService.Cancel(unwrap.Value);unwrap=null;timer.Stop();timer.Dispose();}
}

public sealed class UvTool:Panel
{
    private readonly uint document;
    private readonly MaterialActionQueue actions;
    private readonly Label selection=new(),status=new(){Wrap=WrapMode.Word};
    private readonly DropDown mapping=new();
    private readonly UITimer timer=new(){Interval=.5};
    private bool disposed,documentClosed;
    public bool Busy=>actions.Busy;
    public UvTool(RhinoDoc doc)
    {
        document=doc.RuntimeSerialNumber;actions=new(document,(s,p)=>status.Text=s);
        foreach(var m in new[]{("auto","自动 · 平面 / 箱式"),("xatlas","复杂曲面 · xatlas"),("plane","平面"),("box","箱式"),("cylinder","圆柱侧面")})mapping.Items.Add(new ListItem{Key=m.Item1,Text=m.Item2});mapping.SelectedKey="auto";
        var l=Ui.Layout();l.AddRow(ToolUi.Heading("真实尺寸 UV"));l.AddRow(new Label{Text="准备一次，换材质时复用。1 UV 单位 = 1 米。",Wrap=WrapMode.Word});l.AddRow(selection);l.AddRow(mapping);
        l.AddRow(Ui.Button("准备 / 更新选中物件的 UV",()=>Guard(()=>{var t=ToolUi.Targets(Doc,false);actions.Start(t.Objects,t.Layers,new(){Mode=mapping.SelectedKey!},force:true);})));l.AddRow(Ui.Button("等径管体 · 沿中心线展开…",()=>Guard(()=>RhinoApp.RunScript("_RhinoSceneFlowTubeUV",false))));
        l.AddRow(new Label{Text="复杂曲面需要接缝；砖纹等方向图案的管体优先选中心线展开。材质工具会自动补算缺失的真实尺寸 UV。",Wrap=WrapMode.Word,Width=280});l.AddRow(Ui.Button("取消后续步骤",actions.Cancel));l.AddRow(status);l.AddRow(null);Content=l;
        timer.Elapsed+=(_,_)=>{if(!IsDisposed&&!documentClosed)Guard(()=>selection.Text=$"当前选择 · {ToolUi.Selection(Doc).Length} 个物件");};timer.Start();RhinoDoc.CloseDocument+=OnDocumentClosed;
    }
    private void OnDocumentClosed(object? sender,DocumentEventArgs e){if(e.Document.RuntimeSerialNumber!=document)return;documentClosed=true;timer.Stop();actions.Dispose();}
    private RhinoDoc Doc=>RhinoDoc.FromRuntimeSerialNumber(document)??throw new InvalidOperationException("文档已关闭。");
    private void Guard(Action a){if(disposed||documentClosed)return;try{a();}catch(Exception e){status.Text=e.Message;}}
    public object GetState()=>new{document,busy=Busy,mode=mapping.SelectedKey,status=status.Text};
    protected override void Dispose(bool disposing){if(disposing&&!disposed){disposed=true;RhinoDoc.CloseDocument-=OnDocumentClosed;timer.Stop();timer.Dispose();actions.Dispose();}base.Dispose(disposing);}
}
