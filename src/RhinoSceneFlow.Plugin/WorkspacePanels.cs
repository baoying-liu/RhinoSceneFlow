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
    private static readonly Type[] pages=[typeof(MaterialToolPanel),typeof(UvToolPanel),typeof(PlantToolPanel),typeof(ExportToolPanel)];
    internal static readonly Dictionary<string,WorkspaceHost> Hosts=[];
    internal static readonly HashSet<WorkspaceHost> AllHosts=[];
    private static bool opening;
    internal static void Register(SceneFlowPlugin plugin)
    {
        string[] titles=["SceneFlow · 材质","SceneFlow · UV","SceneFlow · 种植","SceneFlow · PSD"];
        string[] icons=["Materials","Uv","Planting","Export"];
        for(int i=0;i<pages.Length;i++)Panels.RegisterPanel(plugin,pages[i],titles[i],typeof(SceneFlowPlugin).Assembly,"RhinoSceneFlow.Plugin.Resources."+icons[i]+".ico",PanelType.System);
    }
    public static object Open(string page="materials")
    {
        var type=page switch{"materials"=>pages[0],"uv"=>pages[1],"planting"=>pages[2],"export"=>pages[3],_=>throw new ArgumentException("page: materials | uv | planting | export")};
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
    internal static ExportPanel? Export=>Hosts.GetValueOrDefault("export")?.Tool as ExportPanel;
    internal static void Stop()
    {
        // Registered panel controls belong to Rhino. Disposing them here leaves a
        // disposed descendant in Rhino's later UnLoad/DataContext traversal.
        foreach(var host in AllHosts.ToArray())host.Shutdown();Hosts.Clear();AllHosts.Clear();
    }
}

public abstract class WorkspaceHost:Panel,IPanel
{
    private readonly string page;
    private readonly Panel body=new();
    private readonly UITimer documents=new(){Interval=.6};
    private uint serial;
    private bool stopped;
    internal Control? Tool{get;private set;}
    protected WorkspaceHost(string page)
    {
        this.page=page;SceneFlowWorkspace.Hosts[page]=this;SceneFlowWorkspace.AllHosts.Add(this);Padding=new(8);MinimumSize=new(320,300);
        var nav=new DropDown();foreach(var p in new[]{("materials","材质 · AI 与材质库"),("uv","UV · 真实尺寸展开"),("planting","种植 · 即将提供"),("export","PSD · 视图导出")})nav.Items.Add(new ListItem{Key=p.Item1,Text=p.Item2});nav.SelectedKey=page;
        nav.SelectedValueChanged+=(_,_)=>{if(nav.SelectedKey!=page){SceneFlowWorkspace.Open(nav.SelectedKey!);nav.SelectedKey=page;}};
        var menu=new Button{Text="⋯",Width=28,ToolTip="工作区布局"};var context=new ContextMenu();var group=new ButtonMenuItem{Text="将四个工具放入同一容器"};group.Click+=(_,_)=>{try{SceneFlowWorkspace.Group();}catch(Exception e){RhinoApp.WriteLine(e.Message);}};context.Items.Add(group);menu.Click+=(_,_)=>context.Show(menu);
        var navigation=new TableLayout{Spacing=new(6,0),Rows={new TableRow(new TableCell(nav,true),menu)}};
        var root=Ui.Layout();root.AddRow(navigation);root.Add(body,true,true);Content=root;
        Load+=(_,_)=>RefreshDocument();documents.Elapsed+=(_,_)=>RefreshDocument();documents.Start();
    }
    internal void RefreshDocument()
    {
        if(IsDisposed||stopped)return;var doc=RhinoDoc.ActiveDoc;uint next=doc?.RuntimeSerialNumber??0;if(next==serial&&Tool!=null)return;
        if(Tool is ExportPanel {IsExporting:true}||Tool is MaterialsTool {Busy:true}||Tool is UvTool {Busy:true})return;
        body.Content=null;Tool?.Dispose();Tool=null;serial=next;
        if(doc==null){body.Content=new Label{Text="打开 Rhino 模型后开始。"};return;}
        Tool=page switch{"materials"=>new MaterialsTool(doc),"uv"=>new UvTool(doc),"export"=>new ExportPanel(doc),_=>new Label{Text="种植工具\n\n植物素材、面向相机与批量种植将在这里提供。",Wrap=WrapMode.Word}};
        body.Content=Tool;
    }
    public object State()=>new{page,document=serial,details=Tool switch{MaterialsTool m=>m.GetState(),UvTool u=>u.GetState(),ExportPanel e=>e.GetState(),_=>new{placeholder=true}}};
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
[Guid("7AF3B3D7-3243-4D82-A249-85FC9D0244B5")]public sealed class UvToolPanel:WorkspaceHost{public UvToolPanel():base("uv") {}}
[Guid("1912E513-436A-4104-9E1E-A1C7C2D8B006")]public sealed class PlantToolPanel:WorkspaceHost{public PlantToolPanel():base("planting") {}}
[Guid("D49742BA-B6FA-4321-8458-0C6D09F1DB18")]public sealed class ExportToolPanel:WorkspaceHost{public ExportToolPanel():base("export") {}}

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
    private Action? after;
    private bool disposed;
    internal bool Busy=>steps!=null||unwrap!=null;
    internal MaterialActionQueue(uint document,Action<string,int> progress){this.document=document;this.progress=progress;timer.Elapsed+=(_,_)=>Tick();}
    internal void Start(Guid[]? objects,Guid[]? layers,MappingSettings settings,Guid? asset=null,bool force=false)
    {
        if(Busy)throw new InvalidOperationException("正在处理，请等待或取消。");var doc=RhinoDoc.FromRuntimeSerialNumber(document)??throw new InvalidOperationException("文档已关闭。");
        settings.Validate();var ids=MaterialService.ResolveTargets(doc,objects,layers);if(asset.HasValue)MaterialService.Library.Verify(MaterialService.Library.Get(asset.Value));
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
            if(unwrap.HasValue){var job=UnwrapService.Get(unwrap.Value);progress(job.Stage,job.Percent);if(job.Status=="running")return;unwrap=null;var action=after;after=null;if(job.Status=="completed"){action?.Invoke();progress("展开完成"+(action==null?"。":"，材质已应用。"),100);}}
            if(steps!=null){if(steps.Count>0)steps.Dequeue()();if(steps.Count==0)steps=null;}
            if(!Busy)timer.Stop();
        }
        catch(Exception e){steps=null;unwrap=null;after=null;timer.Stop();progress(e.Message,0);}
    }
    internal void Cancel(){steps=null;after=null;if(unwrap.HasValue)UnwrapService.Cancel(unwrap.Value);progress("正在停止后续步骤；已完成的修改可用 Rhino 撤销。",0);}
    public void Dispose(){if(disposed)return;disposed=true;steps=null;after=null;if(unwrap.HasValue)UnwrapService.Cancel(unwrap.Value);unwrap=null;timer.Stop();timer.Dispose();}
}

public sealed class UvTool:Panel
{
    private readonly uint document;
    private readonly MaterialActionQueue actions;
    private readonly Label selection=new(),status=new(){Wrap=WrapMode.Word};
    private readonly DropDown mapping=new();
    private readonly UITimer timer=new(){Interval=.5};
    private bool disposed;
    public bool Busy=>actions.Busy;
    public UvTool(RhinoDoc doc)
    {
        document=doc.RuntimeSerialNumber;actions=new(document,(s,p)=>status.Text=s);
        foreach(var m in new[]{("auto","自动 · 平面 / 箱式"),("xatlas","复杂曲面 · xatlas"),("plane","平面"),("box","箱式"),("cylinder","圆柱侧面")})mapping.Items.Add(new ListItem{Key=m.Item1,Text=m.Item2});mapping.SelectedKey="auto";
        var l=Ui.Layout();l.AddRow(ToolUi.Heading("真实尺寸 UV"));l.AddRow(new Label{Text="准备一次，换材质时复用。1 UV 单位 = 1 米。",Wrap=WrapMode.Word});l.AddRow(selection);l.AddRow(mapping);
        l.AddRow(Ui.Button("准备 / 更新选中物件的 UV",()=>Guard(()=>{var t=ToolUi.Targets(Doc,false);actions.Start(t.Objects,t.Layers,new(){Mode=mapping.SelectedKey!},force:true);})));l.AddRow(Ui.Button("等径管体 · 沿中心线展开…",()=>Guard(()=>RhinoApp.RunScript("_RhinoSceneFlowTubeUV",false))));
        l.AddRow(new Label{Text="复杂曲面需要接缝；砖纹等方向图案的管体优先选中心线展开。材质工具会自动补算缺失的真实尺寸 UV。",Wrap=WrapMode.Word,Width=280});l.AddRow(Ui.Button("取消后续步骤",actions.Cancel));l.AddRow(status);l.AddRow(null);Content=l;
        timer.Elapsed+=(_,_)=>{if(!IsDisposed)selection.Text=$"当前选择 · {ToolUi.Selection(Doc).Length} 个物件";};timer.Start();
    }
    private RhinoDoc Doc=>RhinoDoc.FromRuntimeSerialNumber(document)??throw new InvalidOperationException("文档已关闭。");
    private void Guard(Action a){try{a();}catch(Exception e){status.Text=e.Message;}}
    public object GetState()=>new{document,busy=Busy,mode=mapping.SelectedKey,status=status.Text};
    protected override void Dispose(bool disposing){if(disposing&&!disposed){disposed=true;timer.Stop();timer.Dispose();actions.Dispose();}base.Dispose(disposing);}
}
