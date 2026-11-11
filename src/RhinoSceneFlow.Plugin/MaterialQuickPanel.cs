using Eto.Drawing;
using Eto.Forms;
using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using Rhino.Input.Custom;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

internal static class MaterialSelection
{
    internal static Guid[] Get(RhinoDoc doc)
    {
        using var get=new GetObject();get.SetCommandPrompt("选择需要铺贴材质的物件");
        get.GeometryFilter=ObjectType.Surface|ObjectType.PolysrfFilter|ObjectType.Mesh|ObjectType.Extrusion|ObjectType.SubD;
        get.GetMultiple(1,0);if(get.CommandResult()!=Result.Success)return [];
        return Enumerable.Range(0,get.ObjectCount).Select(i=>get.Object(i).ObjectId).ToArray();
    }
}
public sealed class MaterialQuickCommand : Rhino.Commands.Command
{
    public override string EnglishName=>"RhinoSceneFlowMaterials";
    protected override Result RunCommand(RhinoDoc doc,RunMode mode)
    {
        try{SceneFlowWorkspace.Open("materials");return Result.Success;}
        catch(Exception e){RhinoApp.WriteLine(e.Message);return Result.Failure;}
    }
}
public sealed class WorldUvCommand : Rhino.Commands.Command
{
    public override string EnglishName=>"RhinoSceneFlowWorldUV";
    protected override Result RunCommand(RhinoDoc doc,RunMode mode)
    {
        try
        {
            var ids=MaterialSelection.Get(doc);if(ids.Length==0)return Result.Cancel;
            RhinoApp.WriteLine("检查并计算真实世界 UV…");
            var result=MaterialService.PrepareWorldUv(doc,ids,null,new MappingSettings());
            RhinoApp.WriteLine(MaterialService.Serialize(result));return Result.Success;
        }
        catch(Exception e){RhinoApp.WriteLine(e.Message);return Result.Failure;}
    }
}
public static class MaterialQuickController
{
    private static readonly Dictionary<uint,MaterialQuickPanel> windows=[];
    public static MaterialQuickPanel? Find(uint serial)=>windows.GetValueOrDefault(serial);
    public static MaterialQuickPanel Open(RhinoDoc doc,Guid[]? ids=null)
    {
        NamedViewExportService.RequireActive(doc);ids??=doc.Objects.GetSelectedObjects(false,false).Select(o=>o.Id).ToArray();
        MaterialService.ResolveTargets(doc,ids,null);
        if(windows.TryGetValue(doc.RuntimeSerialNumber,out var running)&&running.Busy)throw new ArgumentException("当前操作尚未完成。");
        if(!doc.Objects.GetSelectedObjects(false,false).Select(o=>o.Id).ToHashSet().SetEquals(ids))
        {doc.Objects.UnselectAll();foreach(var id in ids)doc.Objects.FindId(id)!.Select(true);doc.Views.Redraw();}
        if(windows.TryGetValue(doc.RuntimeSerialNumber,out var old))
        {
            if(old.Busy)throw new ArgumentException("当前任务进行中，请完成后切换目标。");
            old.SetTargets(ids);old.BringToFront();return old;
        }
        var p=new MaterialQuickPanel(doc,ids);windows.Add(doc.RuntimeSerialNumber,p);p.Closed+=(_,_)=>windows.Remove(doc.RuntimeSerialNumber);
        p.Owner=Rhino.UI.RhinoEtoApp.MainWindowForDocument(doc);p.Show();
        var area=Eto.Forms.Screen.PrimaryScreen.WorkingArea;
        if(p.Location.X<area.Left||p.Location.Y<area.Top||p.Location.X+p.Width>area.Right||p.Location.Y+p.Height>area.Bottom)
            p.Location=new Point((int)(area.X+(area.Width-p.Width)/2),(int)(area.Y+(area.Height-p.Height)/2));
        return p;
    }
}
public sealed class MaterialQuickPanel : Form
{
    private readonly uint document;
    private Guid[] targets=[];
    private Guid? selected,jobId,unwrapJob,chatJob;
    private MaterialAsset? selectedVersion;
    private Action? afterUnwrap;
    private readonly MaterialChatView chat;
    private bool closed;
    private readonly TextArea prompt=new(){Height=90,Wrap=true,Text="浅暖灰石灰岩，均匀纹理，无接缝"};
    private readonly UiLabel targetLabel=new(),status=new(){Text="输入描述或选择已有材质。",Wrap=WrapMode.Word,Width=530},referenceLabel=new(){Text="未添加参考图片",Wrap=WrapMode.Word,Width=510};
    private readonly ImageView image=new(){Size=new(500,260)};
    private readonly DropDown assets=new(){Width=350},scope=new(){Width=230},mode=new(){Width=180};
    private readonly NumericStepper width=Ui.Number(.001,1e8,2,120),height=Ui.Number(.001,1e8,2,120),rotation=Ui.Number(-360,360,1),offsetU=Ui.Number(-1e12,1e12,2),offsetV=Ui.Number(-1e12,1e12,2);
    private readonly TabControl tabs=new();
    private readonly ProgressBar progress=new(){MinValue=0,MaxValue=100};
    private readonly UiButton apply,generate,prepare;
    private readonly UITimer timer=new(){Interval=.15};
    private readonly List<string> references=[];
    private readonly List<string> history=[];
    private Queue<Action>? steps;
    private DateTime started;
    private bool selecting;
    public bool Busy=>steps!=null||unwrapJob.HasValue;
    private RhinoDoc Doc=>RhinoDoc.FromRuntimeSerialNumber(document)??throw new InvalidOperationException("文档已关闭。");
    private static TableLayout Row(params Control?[] controls)=>new(){Spacing=new(6,4),Rows={new TableRow(controls.Select(c=>new TableCell(c,c==null)).ToArray())}};
    public MaterialQuickPanel(RhinoDoc doc,Guid[] ids)
    {
        document=doc.RuntimeSerialNumber;Title="RhinoSceneFlow · 给物件上材质";ClientSize=new(580,740);MinimumSize=new(570,690);Padding=new(14);
        width.Value=height.Value=1000;
        scope.Items.Add(new UiListItem{Key="object",Text="应用到该物体"});scope.Items.Add(new UiListItem{Key="layer",Text="应用到该物体所在图层"});scope.SelectedIndex=0;
        foreach(var t in new[]{("auto","自动"),("plane","平面"),("box","箱式"),("cylinder","圆柱侧面"),("xatlas","xatlas 复杂曲面展开")})mode.Items.Add(new UiListItem{Key=t.Item1,Text=t.Item2});mode.SelectedIndex=0;
        apply=Ui.Button("应用材质",()=>Start(false));generate=Ui.Button("生成材质",Generate);prepare=Ui.Button("计算 / 更新真实世界 UV",()=>Start(true));
        var main=Ui.Layout();main.AddRow(targetLabel);main.AddRow(image);main.AddRow(Row(assets,Ui.Button("刷新",RefreshAssets),null));
        main.AddRow(prompt);main.AddRow(Row(Ui.Button("＋参考图片",AddReferences),Ui.Button("清除图片",()=>{references.Clear();RefreshReferences();}),generate,null));main.AddRow(referenceLabel);
        var details=Ui.Layout();details.AddRow(new UiLabel{Text="整张贴图代表的物理尺寸（mm）"});details.AddRow(Row(width,new UiLabel{Text="×"},height,null));
        details.AddRow(new UiLabel{Text="尺寸可从描述确定，但必须由你确认。"});details.AddRow(Row(Ui.Button("保存材质尺寸",SaveSize),null));
        details.AddRow(new UiLabel{Text="UV 每 1 单位对应 1 米，换材质时复用。"});details.AddRow(Row(new UiLabel{Text="映射"},mode,null));
        details.AddRow(Row(new UiLabel{Text="旋转 °"},rotation,null));details.AddRow(Row(new UiLabel{Text="偏移 U / V（mm）"},offsetU,offsetV,null));details.AddRow(prepare);details.AddRow(Ui.Button("沿中心线展开管体…",()=>RhinoApp.RunScript("_RhinoSceneFlowTubeUV",false)));
        details.AddRow(Ui.Button("恢复应用前材质与 UV",()=>Guard(()=>{var t=Target();MaterialService.Restore(Doc,t.Objects,t.Layers);SetStatus("已恢复原材质与 UV。");})));
        details.AddRow(new UiLabel{Text="砖纹 / 木纹等有方向的图案：等径管体优先用“沿中心线展开”，自动分区会留下图案接缝。",Width=510,Wrap=WrapMode.Word});
        details.AddRow(new UiLabel{Text="这里修改的映射参数通过“计算 / 更新”生效。复杂曲面可能有接缝或拉伸。",Width=510,Wrap=WrapMode.Word});
        var library=Ui.Layout();library.AddRow(new UiLabel{Text="导入图片、材质属性、分类和材质包管理"});library.AddRow(new UiLabel{Text="图片生成使用本机 Codex 的 ChatGPT 登录；未安装或未登录时会明确提示。",Width=510,Wrap=WrapMode.Word});library.AddRow(Ui.Button("打开完整材质库",()=>MaterialPanelController.Open(Doc)));
        chat=new(document,()=> (width.Value/1000,height.Value/1000),id=>{chatJob=id;progress.Indeterminate=true;});
        tabs.Pages.Add(new TabPage{Text="对话生成",Content=chat});tabs.Pages.Add(new TabPage{Text="快捷生成",Content=main});
        Shown+=async(_,_)=>{if(!closed)await chat.StartAsync();};tabs.Pages.Add(new TabPage{Text="尺寸与铺贴",Content=details});tabs.Pages.Add(new TabPage{Text="材质库 / 属性",Content=library});
        var root=Ui.Layout();root.Add(tabs,true,true);root.AddRow(Row(new UiLabel{Text="应用范围"},scope,null));root.AddRow(progress);root.AddRow(status);root.AddRow(Row(Ui.Button("取消后续步骤",Cancel),null,apply));Content=root;
        assets.SelectedValueChanged+=(_,_)=>{if(!selecting)Guard(()=>{if(Guid.TryParse(assets.SelectedKey,out var id))SelectAsset(id);});};
        timer.Elapsed+=(_,_)=>Tick();timer.Start();SetTargets(ids);RefreshAssets();
        jobId=MaterialGeneration.ActiveJobId;
        if(jobId.HasValue){started=MaterialGeneration.Get(jobId.Value).CreatedUtc;progress.Indeterminate=true;apply.Enabled=generate.Enabled=false;SetStatus("继续显示正在进行的图片生成任务。");}
        RhinoDoc.CloseDocument+=ClosedDoc;Closed+=(_,_)=>{closed=true;chat.Dispose();RhinoDoc.CloseDocument-=ClosedDoc;steps=null;timer.Stop();timer.Dispose();var b=image.Image;image.Image=null;b?.Dispose();};
        Closing+=(_,e)=>{if(Busy){e.Cancel=true;SetStatus("正在处理，请先取消后续步骤。");}};
    }
    private void ClosedDoc(object? s,DocumentEventArgs e){if(e.Document.RuntimeSerialNumber==document){steps=null;Close();}}
    private void Guard(Action action){try{action();}catch(Exception e){SetStatus(e.Message);}}
    private void SetStatus(string text){status.Text=text;history.Add(text);if(history.Count>100)history.RemoveAt(0);}
    public void SetTargets(Guid[] ids){targets=ids.Distinct().Order().ToArray();UpdateTargetLabel();}
    private void UpdateTargetLabel()=>targetLabel.Text=targets.Length==0?"当前未选中物体，请先在 Rhino 中选择。":$"当前选择：{targets.Length} 个物体 · {string.Join("、",targets.Take(2).Select(id=>Doc.Objects.FindId(id)?.Attributes.Name is {Length:>0} name?name:id.ToString()[..8]))}";
    private void RefreshTargets()
    {
        var current=Doc.Objects.GetSelectedObjects(false,false).Select(o=>o.Id).Distinct().Order().ToArray();
        if(!targets.SequenceEqual(current)){targets=current;UpdateTargetLabel();}
    }
    private (Guid[]? Objects,Guid[]? Layers) Target()
    {
        RefreshTargets();
        if(targets.Length==0)throw new ArgumentException("当前没有选中的物体。请先在 Rhino 中选择，再应用材质。");
        if(scope.SelectedKey!="layer")return(targets.ToArray(),null);
        return(null,targets.Select(id=>Doc.Objects.FindId(id)??throw new ArgumentException("原物件已删除。")).Select(o=>Doc.Layers[o.Attributes.LayerIndex].Id).Distinct().ToArray());
    }
    public void RefreshAssets()
    {
        selecting=true;try{assets.Items.Clear();foreach(var a in MaterialService.Library.List())assets.Items.Add(new UiListItem{Key=a.Id.ToString(),Text=a.Name});if(selected.HasValue)assets.SelectedKey=selected.ToString();}finally{selecting=false;}
    }
    public void SelectAsset(Guid id)
    {
        var a=MaterialService.Library.Get(id);selected=id;selectedVersion=MaterialLibrary.Clone(a);selecting=true;assets.SelectedKey=id.ToString();selecting=false;width.Value=a.WidthMeters*1000;height.Value=a.HeightMeters*1000;
        using var src=new System.Drawing.Bitmap(MaterialService.Library.MapPath(a,"baseColor"));using var bitmap=new System.Drawing.Bitmap(500,260);using var g=System.Drawing.Graphics.FromImage(bitmap);g.Clear(System.Drawing.Color.WhiteSmoke);
        double ratio=Math.Min(500.0/src.Width,260.0/src.Height);int w=(int)(src.Width*ratio),h=(int)(src.Height*ratio);g.DrawImage(src,(500-w)/2,(260-h)/2,w,h);
        var old=image.Image;image.Image=Ui.Bitmap(bitmap);old?.Dispose();
    }
    private void AddReferences()=>Guard(()=>{if(Busy)return;using var d=new OpenFileDialog{MultiSelect=true};d.Filters.Add(new FileFilter("参考图片",".png",".jpg",".jpeg"));if(d.ShowDialog(this)==DialogResult.Ok){if(references.Count+d.Filenames.Count()>8)throw new ArgumentException("最多 8 张参考图片。");references.AddRange(d.Filenames);RefreshReferences();}});
    private void RefreshReferences()=>referenceLabel.Text=references.Count==0?"未添加参考图片":string.Join(" · ",references.Select(Path.GetFileName));
    private void Generate()=>Guard(()=>
    {
        if(Busy)throw new ArgumentException("请先等待当前操作完成。");if(jobId.HasValue&&MaterialGeneration.Get(jobId.Value).Status is "pending" or "running")throw new ArgumentException("已有生成任务，请先完成或取消。");
        var job=MaterialGeneration.Start(new MaterialAsset{Name="AI 材质 "+DateTime.Now.ToString("HHmmss"),WidthMeters=width.Value/1000,HeightMeters=height.Value/1000},prompt.Text,references.ToArray());jobId=job.Id;started=DateTime.UtcNow;progress.Value=0;progress.Indeterminate=true;apply.Enabled=generate.Enabled=false;SetStatus("正在启动本机 Codex，生成完成后会自动显示新图片。");
    });
    private void SaveSize()=>Guard(()=>{if(selectedVersion==null)throw new ArgumentException("请先选择材质。");var a=MaterialLibrary.Clone(selectedVersion);a.WidthMeters=width.Value/1000;a.HeightMeters=height.Value/1000;a=MaterialService.Library.Update(a);RefreshAssets();SelectAsset(a.Id);SetStatus("材质尺寸已保存，应用后生效；不需要重新计算 UV。");});
    private MappingSettings Settings()=>new(){Mode=mode.SelectedKey??"auto",Rotation=rotation.Value,OffsetUMeters=offsetU.Value/1000,OffsetVMeters=offsetV.Value/1000};
    private void Start(bool uvOnly)=>Guard(()=>
    {
        if(Busy)throw new ArgumentException("正在处理。");var t=Target();var ids=MaterialService.ResolveTargets(Doc,t.Objects,t.Layers);var settings=Settings();
        Guid? asset=selected;if(!uvOnly)
        {
            if(asset==null)throw new ArgumentException("请先生成或选择材质。");var a=MaterialService.Library.Get(asset.Value);
            if(a.WidthMeters!=width.Value/1000||a.HeightMeters!=height.Value/1000)throw new ArgumentException("尺寸已修改，请先在“尺寸与铺贴”保存。");
        }
        // Snapshot the current selection once for this operation; later clicks use a fresh selection.
        if(settings.Mode=="xatlas"||ids.Any(id=>MaterialService.ReadUv(Doc.Objects.FindId(id)!)?.Mode=="xatlas"&&!MaterialService.UvValid(Doc,Doc.Objects.FindId(id)!)))
        {
            var job=UnwrapService.Start(Doc,t.Objects,t.Layers);unwrapJob=job.Id;
            afterUnwrap=uvOnly?null:()=>MaterialService.Apply(Doc,asset!.Value,t.Objects,t.Layers,new MappingSettings());
            apply.Enabled=generate.Enabled=prepare.Enabled=scope.Enabled=tabs.Enabled=false;SetStatus("正在用 xatlas 展开复杂曲面…");return;
        }
        if(uvOnly)MaterialService.PrepareWorldUv(Doc,t.Objects,t.Layers,settings,true,true);
        else MaterialService.Apply(Doc,asset!.Value,t.Objects,t.Layers,settings,true);
        var queue=new Queue<Action>();int computed=0,reused=0,done=0;
        foreach(var id in ids)queue.Enqueue(()=>
        {
            using var result=System.Text.Json.JsonDocument.Parse(MaterialService.Serialize(MaterialService.PrepareWorldUv(Doc,[id],null,settings,uvOnly)));
            computed+=result.RootElement.GetProperty("computed").GetInt32();reused+=result.RootElement.GetProperty("reused").GetInt32();done++;
            progress.Value=(int)(90.0*done/ids.Length);SetStatus($"真实世界 UV {done}/{ids.Length}：计算 {computed}，复用 {reused}。");
        });
        queue.Enqueue(()=>{if(!uvOnly){MaterialService.Apply(Doc,asset!.Value,t.Objects,t.Layers,settings);SetStatus($"材质已应用。UV 计算 {computed}，复用 {reused}。");}else SetStatus($"UV 已完成。计算 {computed}，复用 {reused}。");progress.Value=100;});
        steps=queue;progress.Indeterminate=false;apply.Enabled=generate.Enabled=prepare.Enabled=scope.Enabled=tabs.Enabled=false;progress.Value=0;SetStatus("检查真实世界 UV…");
    });
    private void Cancel()=>Guard(()=>{if(unwrapJob.HasValue){afterUnwrap=null;UnwrapService.Cancel(unwrapJob.Value);}if(chatJob.HasValue)MaterialChat.Cancel(chatJob.Value);if(steps!=null){steps=null;Unlock();SetStatus("后续步骤已取消，已完成的 UV 可保留或用 Rhino 撤销。");}if(jobId.HasValue){var j=MaterialGeneration.Get(jobId.Value);if(j.Status is "pending" or "running")MaterialGeneration.Cancel(j.Id);jobId=null;progress.Indeterminate=false;progress.Value=0;SetStatus("生成任务已取消。");}Unlock();});
    private void Unlock(){apply.Enabled=generate.Enabled=prepare.Enabled=scope.Enabled=tabs.Enabled=true;apply.Enabled=generate.Enabled=jobId==null;}
    private void Tick()
    {
        if(closed)return;
        if(chatJob.HasValue)
        {
            var j=MaterialChat.Get(chatJob.Value);status.Text=j.Stage;
            if(j.Status!="running"){chatJob=null;progress.Indeterminate=false;SetStatus(j.Stage);if(j.Material.HasValue){RefreshAssets();SelectAsset(j.Material.Value);}}
        }
        if(unwrapJob.HasValue)
        {
            var j=UnwrapService.Get(unwrapJob.Value);status.Text=j.Stage;progress.Value=j.Percent;
            if(j.Status!="running"){unwrapJob=null;var action=afterUnwrap;afterUnwrap=null;Unlock();if(j.Status=="completed")Guard(()=>{action?.Invoke();SetStatus("xatlas 展开完成"+(action==null?"。":"，材质已应用。"));});else SetStatus(j.Stage);}
            return;
        }
        if(steps!=null)
        {
            try{if(steps.Count>0)steps.Dequeue()();if(steps.Count==0){steps=null;Unlock();}}
            catch(Exception e){steps=null;Unlock();SetStatus("处理失败："+e.Message+"；已完成步骤可用 Rhino 撤销。");}
            return;
        }
        Guard(RefreshTargets);
        if(jobId==null)return;
        Guard(()=>{var job=MaterialGeneration.Get(jobId.Value);status.Text=$"{job.Stage} · 已用 {(DateTime.UtcNow-started).TotalSeconds:F0} 秒";
            if(job.Status=="completed"&&job.Material.HasValue){RefreshAssets();SelectAsset(job.Material.Value);jobId=null;progress.Indeterminate=false;progress.Value=100;Unlock();SetStatus("材质已生成。请确认物理尺寸，再应用。 ");}
            else if(job.Status=="cancelled"){jobId=null;progress.Indeterminate=false;progress.Value=0;Unlock();SetStatus("生成任务已取消。");}
            else if(job.Status=="failed"){jobId=null;progress.Indeterminate=false;progress.Value=0;Unlock();SetStatus(job.Stage+"；可点击生成材质重试。");}});
    }
    public object GetState()=>new{open=true,document,targets,selected,jobId,unwrapJob,chatJob,chatKit=chat.State,busy=Busy,scope=scope.SelectedKey,progress=progress.Value,status=status.Text,history=history.ToArray()};
}

public sealed class UnwrapCommand : Rhino.Commands.Command
{
    public override string EnglishName=>"RhinoSceneFlowUnwrap";
    protected override Result RunCommand(RhinoDoc doc,RunMode mode)
    {
        try{var ids=MaterialSelection.Get(doc);if(ids.Length==0)return Result.Cancel;var job=UnwrapService.Start(doc,ids,null);RhinoApp.WriteLine("xatlas 后台展开已启动："+job.Id);return Result.Success;}
        catch(Exception e){RhinoApp.WriteLine(e.Message);return Result.Failure;}
    }
}
