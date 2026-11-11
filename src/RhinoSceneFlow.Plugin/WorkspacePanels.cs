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
    private static readonly Type[] pages=[typeof(MaterialToolPanel),typeof(MaterialLibraryToolPanel),typeof(UvToolPanel),typeof(PlantToolPanel),typeof(ExportToolPanel),typeof(PlantsListToolPanel),typeof(PropertiesToolPanel),typeof(PostProductionToolPanel),typeof(SettingsToolPanel)];
    private static readonly Dictionary<uint,Guid> selectedAssets=[];
    private static readonly Dictionary<uint,string> materialScopes=[];
    internal static readonly Dictionary<string,WorkspaceHost> Hosts=[];
    internal static readonly HashSet<WorkspaceHost> AllHosts=[];
    private static bool opening;
    internal static void Register(SceneFlowPlugin plugin)
    {
        string[] titles=["SceneFlow · AI 素材","SceneFlow · 材质库","SceneFlow · UV","SceneFlow · 种植","SceneFlow · PSD","SceneFlow · Plants List","SceneFlow · 属性","SceneFlow · AI 后期","SceneFlow · 设置"];
        string[] icons=["Materials","Library","Uv","Planting","Export","PlantsList","Properties","PostProduction","Settings"];
        for(int i=0;i<pages.Length;i++)Panels.RegisterPanel(plugin,pages[i],WorkspaceAppearance.Text(titles[i]),typeof(SceneFlowPlugin).Assembly,"RhinoSceneFlow.Plugin.Resources."+icons[i]+".ico",PanelType.System);
        RhinoDoc.CloseDocument+=OnDocumentClosed;
    }
    private static void OnDocumentClosed(object? sender,DocumentEventArgs e){uint serial=e.Document.RuntimeSerialNumber;selectedAssets.Remove(serial);materialScopes.Remove(serial);UnwrapService.CancelDocument(serial);RandomTextureService.CancelDocument(serial);}
    public static object Open(string page="materials")
    {
        var type=page switch{"materials"=>pages[0],"library"=>pages[1],"uv"=>pages[2],"planting"=>pages[3],"export"=>pages[4],"plantsList"=>pages[5],"properties"=>pages[6],"post"=>pages[7],"settings"=>pages[8],_=>throw new ArgumentException("page: materials | library | uv | planting | export | plantsList | properties | post | settings")};
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
    internal static void RefreshAppearance(PluginPreferences preferences)
    {
        UiPresentation.Refresh(preferences);
        foreach(var host in AllHosts.ToArray().Where(h=>!h.IsDisposed))
        {
            if(host.Tool is SettingsTool settings)settings.SyncAppearance(preferences);
            if(host.Tool is MaterialsTool materials)materials.RefreshPresentation();
            WorkspaceAppearance.Apply(host);
        }
    }
    internal static void RefreshCatalog(){foreach(var tool in AllHosts.Select(h=>h.Tool).OfType<MaterialsTool>().ToArray())tool.ReloadCatalog();}
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
        RhinoDoc.CloseDocument-=OnDocumentClosed;NamedViewUndo.Stop();
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
        this.page=page;SceneFlowWorkspace.Hosts[page]=this;SceneFlowWorkspace.AllHosts.Add(this);Padding=new(10);MinimumSize=new(240,300);
        var nav=new DropDown{Width=100};foreach(var p in new[]{("materials","AI · 素材对话"),("library","材质库 · 浏览与应用"),("uv","UV · 真实尺寸展开"),("planting","植物库 · 种植"),("plantsList","Plants List · 组合管理"),("properties","属性 · 当前选择"),("export","PSD · 视图导出"),("post","AI 后期 · Web 工作台"),("settings","设置 · SceneFlow")})nav.Items.Add(new UiListItem{Key=p.Item1,Text=p.Item2});nav.SelectedKey=page;
        nav.SelectedValueChanged+=(_,_)=>{if(nav.SelectedKey!=page){SceneFlowWorkspace.Open(nav.SelectedKey!);nav.SelectedKey=page;}};
        var menu=new UiButton{Text="⋯",Width=28,ToolTip="工作区布局"};var context=new ContextMenu();var group=new UiButtonMenuItem{Text="将所有工具放入同一容器"};group.Click+=(_,_)=>{try{SceneFlowWorkspace.Group();}catch(Exception e){RhinoApp.WriteLine(e.Message);}};context.Items.Add(group);menu.Click+=(_,_)=>{group.Text=WorkspaceAppearance.Text("将所有工具放入同一容器");context.Show(menu);};
        var settings=new UiButton{Text="⚙",Width=28,ToolTip="SceneFlow 设置 / Settings"};settings.Click+=(_,_)=>PluginPreferences.Show();
        var navigation=new TableLayout{Spacing=new(6,0),Rows={new TableRow(new TableCell(nav,true),settings,menu)}};
        var root=Ui.Layout();root.AddRow(navigation);root.Add(body,true,true);Content=root;
        Load+=(_,_)=>RefreshDocument();documents.Elapsed+=(_,_)=>RefreshDocument();documents.Start();
    }
    internal void RefreshDocument()
    {
        if(IsDisposed||stopped||rebinding)return;var doc=RhinoDoc.ActiveDoc;
        if(doc!=null&&(!doc.IsAvailable||doc.IsClosing||doc.IsOpening||doc.IsCreating||doc.IsInitializing))return;
        uint next=page=="settings"?0:doc?.RuntimeSerialNumber??0;if(next==serial&&Tool!=null)return;
        if(Tool is ExportPanel {IsExporting:true}||Tool is MaterialsTool {Busy:true}||Tool is UvTool {Busy:true})return;
        rebinding=true;
        try
        {
            body.Content=null;var old=Tool;Tool=null;old?.Dispose();serial=next;error=null;
            Tool=page=="settings"?new SettingsTool():doc==null?new UiLabel{Text="打开 Rhino 模型后开始。"}:page switch{"materials"=>new MaterialsTool(doc),"library"=>new MaterialsTool(doc,true),"uv"=>new UvTool(doc),"export"=>new ExportPanel(doc),"planting"=>new PlantTool(doc),"plantsList"=>new PlantsListTool(doc),"properties"=>new PropertiesTool(doc),"post"=>new PostProductionTool(doc),_=>new UiLabel{Text="打开工具"}};
            body.Content=Tool;WorkspaceAppearance.Apply(this);
        }
        catch(Exception e){serial=next;error=e.ToString();Tool=new UiLabel{Text="工具切换文档失败："+e.Message,Wrap=WrapMode.Word};body.Content=Tool;WorkspaceAppearance.Apply(this);RhinoApp.WriteLine(error);}
        finally{rebinding=false;}
    }
    public object State()=>new{page,document=serial,error,details=Tool switch{MaterialsTool m=>m.GetState(),UvTool u=>u.GetState(),ExportPanel e=>e.GetState(),PlantTool p=>p.State(),PlantsListTool l=>l.State(),PropertiesTool p=>p.State(),PostProductionTool p=>p.State(),SettingsTool s=>s.State(),_=>new{placeholder=true}}};
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
[Guid("A484592D-B362-468F-AB6E-5F73106520F4")]public sealed class SettingsToolPanel:WorkspaceHost{public SettingsToolPanel():base("settings") {}}

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
    // Constrain only the page scroller. Inner text editors and data grids retain
    // their own scrolling; Eto WPF wraps the ScrollViewer in an EtoBorder.
    internal static Scrollable VerticalScroll(Control content,int height=-1)
    {
        var scroll=new Scrollable{Content=content,ExpandContentWidth=true,ExpandContentHeight=false,Border=BorderType.None};
        if(height>0)scroll.Height=height;
        var native=scroll.ControlObject;
        if(native is System.Windows.Controls.Border border)native=border.Child;
        if(native is System.Windows.Controls.ScrollViewer viewer)
            viewer.HorizontalScrollBarVisibility=System.Windows.Controls.ScrollBarVisibility.Disabled;
        return scroll;
    }
    internal static TableLayout Row(params Control?[] controls)=>new(){Spacing=new(6,4),Rows={new TableRow(controls.Select(c=>new TableCell(c,c==null)).ToArray())}};
    internal static UiLabel Heading(string text)=>new(){Text=text,Font=new Font(SystemFont.Bold,11),Wrap=WrapMode.Word};
    internal static UiLabel Note(string text)=>new(){Text=text,Wrap=WrapMode.Word};
    internal static UiGroupBox Section(string title,Control content)=>new(){Text=title,Content=new Panel{Padding=new(8),Content=content}};
    internal static UiExpander Help(string text)=>new(){Header="使用说明",Content=Note(text),Expanded=false};
    internal static TableLayout Pair(Control first,Control second)=>new(){Tag="presentation-pair",Spacing=new(6,4),Rows={new TableRow(new TableCell(first,true),new TableCell(second,true))}};
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
    private readonly UiLabel selection=new(),status=new(){Wrap=WrapMode.Word};
    private readonly DropDown mapping=new(){Width=100};
    private readonly UiButton prepare,cancel;
    private readonly UITimer timer=new(){Interval=.5};
    private bool disposed,documentClosed;
    public bool Busy=>actions.Busy;
    public UvTool(RhinoDoc doc)
    {
        document=doc.RuntimeSerialNumber;actions=new(document,(s,p)=>status.Text=s);
        foreach(var m in new[]{("auto","自动 · 平面 / 箱式"),("xatlas","复杂曲面 · xatlas"),("plane","平面"),("box","箱式"),("cylinder","圆柱侧面")})mapping.Items.Add(new UiListItem{Key=m.Item1,Text=m.Item2});mapping.SelectedKey="auto";
        var l=Ui.Layout();l.AddRow(ToolUi.Heading("真实尺寸 UV"));l.AddRow(ToolUi.Note("准备一次，换材质时复用 · 1 UV 单位 = 1 米"));l.AddRow(selection);
        prepare=Ui.Button("准备 / 更新 UV",()=>Guard(()=>{var t=ToolUi.Targets(Doc,false);actions.Start(t.Objects,t.Layers,new(){Mode=mapping.SelectedKey!},force:true);}));
        var basic=Ui.Layout();basic.AddRow(new UiLabel{Text="展开方式"});basic.AddRow(mapping);basic.AddRow(prepare);l.AddRow(ToolUi.Section("选中物件",basic));
        var tube=Ui.Layout();tube.AddRow(ToolUi.Note("适用于砖纹、网格等有方向的等径管体。"));tube.AddRow(Ui.Button("选择管体与中心线…",()=>Guard(()=>RhinoApp.RunScript("_RhinoSceneFlowTubeUV",false))));l.AddRow(new UiExpander{Header="管体专用展开",Content=tube});
        l.AddRow(ToolUi.Help("复杂曲面需要接缝。材质工具会自动补算缺失的真实尺寸 UV，通常无需手动准备。"));cancel=Ui.Button("取消后续步骤",actions.Cancel);cancel.Visible=false;l.AddRow(status);l.AddRow(cancel);l.AddRow(null);Content=ToolUi.VerticalScroll(l);
        void Sync(){if(IsDisposed||documentClosed)return;Guard(()=>{int count=ToolUi.Selection(Doc).Length;selection.Text=count>0?$"当前选择 · {count} 个物件":"先在 Rhino 中选择需要展开的物件";prepare.Enabled=count>0&&!Busy;mapping.Enabled=!Busy;cancel.Visible=Busy;});}
        timer.Elapsed+=(_,_)=>Sync();timer.Start();Sync();RhinoDoc.CloseDocument+=OnDocumentClosed;
    }
    private void OnDocumentClosed(object? sender,DocumentEventArgs e){if(e.Document.RuntimeSerialNumber!=document)return;documentClosed=true;timer.Stop();actions.Dispose();}
    private RhinoDoc Doc=>RhinoDoc.FromRuntimeSerialNumber(document)??throw new InvalidOperationException("文档已关闭。");
    private void Guard(Action a){if(disposed||documentClosed)return;try{a();}catch(Exception e){status.Text=e.Message;}}
    public object GetState()=>new{document,busy=Busy,mode=mapping.SelectedKey,status=status.Text};
    protected override void Dispose(bool disposing){if(disposing&&!disposed){disposed=true;RhinoDoc.CloseDocument-=OnDocumentClosed;timer.Stop();timer.Dispose();actions.Dispose();}base.Dispose(disposing);}
}

public sealed class SettingsCommand:Rhino.Commands.Command
{public override string EnglishName=>"RhinoSceneFlowSettings";protected override Rhino.Commands.Result RunCommand(RhinoDoc doc,Rhino.Commands.RunMode mode){SceneFlowWorkspace.Open("settings");return Rhino.Commands.Result.Success;}}
