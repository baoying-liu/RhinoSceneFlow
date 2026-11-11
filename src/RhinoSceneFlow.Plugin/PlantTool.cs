using Eto.Forms;
using Eto.Drawing;
using Rhino;
using Rhino.Geometry;
using Rhino.Input;
using Rhino.Input.Custom;
using RhinoSceneFlow.Core;
using System.Text.Json;
namespace RhinoSceneFlow.Plugin;

public sealed class PlantTool:Panel
{
    private static readonly HashSet<PlantTool> tools=[];
    private readonly uint document;
    private readonly TextBox query=new(){PlaceholderText="搜索名称、学名、科属或标签"},name=new(){Text="种植组合"};
    private readonly PlantShelf list=new(235),palette=new(180,true);
    private readonly DropDown language=new(){Width=110},libraryView=new(){Width=85},compositionView=new(){Width=85};
    private readonly Label status=new(){Wrap=WrapMode.Word,Width=270},context=new(){Wrap=WrapMode.Word,Width=270};
    private readonly NumericStepper density=Ui.Number(0,1000,3),layoutSeed=Seed(),sizeSeed=Seed(),mirrorSeed=Seed(),spacing=Ui.Number(0,1000,2),weight=Ui.Number(.001,1000,3),edgeDistance=Ui.Number(0,10000,2),edgeStrength=Ui.Number(0,1,2),angle=Ui.Number(10,85);
    private readonly NumericStepper[] curve=Enumerable.Range(0,5).Select(_=>Ui.Number(0,1,2,48)).ToArray();
    private readonly PlantScaleSlider minimum=new("最小比例",.5,1,.75),maximum=new("最大比例",1,2,1.5);
    private readonly CheckBox mirror=new(){Text="随机水平镜像",Checked=true},ignoreSpacing=new(){Text="突破植物间距"},edgeDensity=new(){Text="影响自动密度",Checked=true},edgeSize=new(){Text="影响植物大小",Checked=true};
    private readonly DropDown facing=new();private readonly UITimer poll=new(){Interval=.3};
    private readonly Expander libraryExpander=new(){Header="植物库",Expanded=true};
    private PlantGroupSpec draft=new();private Guid? selected,group,catalogJob,namesJob;private bool stopped,binding,pending;private DateTime changed;private string catalogSignature="",selectionSignature="",boundSpec="",namesAttempt="";
    private RhinoDoc Doc=>RhinoDoc.FromRuntimeSerialNumber(document)??throw new InvalidOperationException("文档已关闭。");
    private static NumericStepper Seed()=>Ui.Number(int.MinValue,int.MaxValue,0,115);
    internal static void StopDocument(uint serial){foreach(var t in tools.Where(t=>t.document==serial).ToArray())t.Stop();}
    internal static void PresentationChanged(){foreach(var t in tools.Where(t=>!t.stopped).ToArray())t.Guard(t.RefreshPresentation);}
    private readonly bool propertiesOnly;
    private readonly SeasonalAssetPanel seasonal=new(true);
    public PlantTool(RhinoDoc doc,bool propertiesOnly=false)
    {
        document=doc.RuntimeSerialNumber;this.propertiesOnly=propertiesOnly;tools.Add(this);
        foreach(var (key,text) in new[]{("auto","跟随 Rhino"),("zh","中文"),("en","English")})language.Items.Add(new ListItem{Key=key,Text=text});
        foreach(var picker in new[]{libraryView,compositionView})foreach(var (key,text) in new[]{("tiles","小方块"),("list","列表")})picker.Items.Add(new ListItem{Key=key,Text=text});
        var library=Ui.Layout();library.AddRow(Ui.Button("在 AI 对话中生成植物",()=>SceneFlowWorkspace.Open("materials")));library.AddRow(query);library.AddRow(ToolUi.Row(new Label{Text="显示方式"},libraryView,null));library.AddRow(list);
        library.AddRow(ToolUi.Pair(Ui.Button("加入组合 ↓",()=>Guard(AddSelected)),Ui.Button("刷新植物库",()=>Guard(Refresh))));library.AddRow(seasonal);
        var management=Ui.Layout();management.AddRow(Ui.Button("AI 整理分类与标签",()=>Guard(()=>{catalogJob=CatalogService.Organize(true).Id;})));management.AddRow(Ui.Button("界面与名称语言设置",PluginPreferences.Show));library.AddRow(new Expander{Header="植物库管理",Content=management});
        var composition=Ui.Layout();composition.AddRow(ToolUi.Row(ToolUi.Note("拖入或双击库中植物"),null,compositionView));composition.AddRow(palette);composition.AddRow(ToolUi.Row(new Label{Text="数量比重"},weight,null));composition.AddRow(ToolUi.Row(new Label{Text="植物间距 m"},spacing,null));composition.AddRow(Ui.Button("从组合中移除所选类型",()=>Guard(RemoveSelected)));
        var general=Ui.Layout();general.AddRow(ToolUi.Row(new Label{Text="密度 株/m²"},density,null));general.AddRow(ignoreSpacing);general.AddRow(ToolUi.Row(new Label{Text="Layout Seed"},layoutSeed,null));general.AddRow(ToolUi.Row(new Label{Text="大小 Seed"},sizeSeed,null));general.AddRow(minimum);general.AddRow(maximum);general.AddRow(mirror);general.AddRow(ToolUi.Row(new Label{Text="Mirror Seed"},mirrorSeed,null));
        var edge=Ui.Layout();edge.AddRow(ToolUi.Row(new Label{Text="边缘距离 m"},edgeDistance,null));edge.AddRow(ToolUi.Row(new Label{Text="强度 0–1"},edgeStrength,null));edge.AddRow(ToolUi.Row(edgeDensity,edgeSize,null));edge.AddRow(new Label{Text="衰减曲线：边界 0% → 内部 100%",Wrap=WrapMode.Word});edge.AddRow(new PlantCurvePreview(curve));edge.AddRow(ToolUi.Row(curve.Cast<Control?>().ToArray()));edge.AddRow(new Label{Text="手工植物保留位置，只参与大小衰减。",Wrap=WrapMode.Word});
        foreach(var (key,text) in new[]{("auto","自动朝向"),("z","只绕 Z 轴"),("free","完全朝向相机")})facing.Items.Add(new ListItem{Key=key,Text=text});facing.SelectedKey=PlantService.Settings.Mode;angle.Value=PlantService.Settings.Angle;
        var global=Ui.Layout();global.AddRow(Ui.Button("打开全局植物显示设置",PluginPreferences.Show));
        libraryExpander.Content=library;var body=Ui.Layout();if(!propertiesOnly)body.AddRow(libraryExpander);body.AddRow(ToolUi.Section("待种植植物",composition));body.AddRow(new Expander{Header="密度、大小与随机",Content=general,Expanded=false});body.AddRow(new Expander{Header="边缘衰减",Content=edge});body.AddRow(new Expander{Header="全局相机朝向",Content=global});
        var root=Ui.Layout();root.AddRow(ToolUi.Heading(propertiesOnly?"组合参数":"植物库与种植"));root.AddRow(context);root.AddRow(new Label{Text="组合名称"});if(propertiesOnly)root.AddRow(name);else root.AddRow(new TableLayout{Spacing=new(6,0),Rows={new TableRow(new TableCell(name,true),Ui.Button("新建",NewDraft))}});root.Add(new Scrollable{Content=body,ExpandContentWidth=true},true,true);
        var placement=Ui.Layout();placement.AddRow(Ui.Button("在曲面上生成 / 重新关联",()=>Guard(Scatter)));placement.AddRow(Ui.Button("连续点种 · Esc 结束",()=>Guard(PlacePoint)));root.AddRow(ToolUi.Section("放置植物",placement));root.AddRow(status);Content=root;
        query.TextChanged+=(_,_)=>RefreshList();list.SelectionChanged+=id=>{if(!binding)Guard(()=>Select(id));};list.Activated+=id=>Guard(()=>{Select(id);AddSelected();});
        palette.SelectionChanged+=_=>PaletteFields();spacing.ValueChanged+=(_,_)=>PaletteChanged();weight.ValueChanged+=(_,_)=>PaletteChanged();
        foreach(var n in new[]{density,layoutSeed,sizeSeed,mirrorSeed,edgeDistance,edgeStrength}.Concat(curve))n.ValueChanged+=(_,_)=>Changed();foreach(var c in new[]{mirror,ignoreSpacing,edgeDensity,edgeSize})c.CheckedChanged+=(_,_)=>Changed();minimum.Changed+=Changed;maximum.Changed+=Changed;name.TextChanged+=(_,_)=>Changed();
        palette.AssetDropped+=id=>Guard(()=>{Select(id);AddSelected();});
        foreach(var picker in new[]{language,libraryView,compositionView})picker.SelectedValueChanged+=(_,_)=>{if(!binding)Guard(()=>PlantUiPreferences.Save(new(){Language=language.SelectedKey??"auto",LibraryView=libraryView.SelectedKey??"tiles",CompositionView=compositionView.SelectedKey??"tiles"}));};
        Bind();RefreshPresentation();poll.Elapsed+=(_,_)=>Guard(Poll);poll.Start();if(propertiesOnly)Poll();
    }
    public void Select(Guid id)
    {
        seasonal.Bind(id);
        var a=PlantService.Library.Get(id);if(a.Plant==null)throw new ArgumentException("不是植物素材。");selected=id;PlantService.Selected[document]=id;libraryExpander.Expanded=true;
        binding=true;try{list.SelectedKey=id.ToString();}finally{binding=false;}
    }
    private void RefreshPresentation()
    {
        var p=PlantUiPreferences.Load();binding=true;try{language.SelectedKey=p.Language;libraryView.SelectedKey=p.LibraryView;compositionView.SelectedKey=p.CompositionView;list.View=p.LibraryView;palette.View=p.CompositionView;}finally{binding=false;}Refresh();PaletteList();
    }
    private static PlantShelfItem Item(MaterialAsset a,string lang)
    {
        string path="";try{path=PlantService.Library.MapPath(a,"baseColor");}catch(IOException){}catch(InvalidDataException){}
        return new(a.Id,a.Plant!.ScientificName,PlantNames.Display(a,lang),path);
    }
    public void Refresh(){if(stopped)return;catalogSignature=string.Join(";",PlantService.Library.List().Select(a=>$"{a.Id}:{a.Revision}:{a.CatalogRevision}"));RefreshList();}
    private void RefreshList()
    {
        if(stopped||binding)return;binding=true;try{var lang=PlantUiPreferences.Load().ResolvedLanguage;list.SetItems(PlantService.Library.List().Where(a=>(a.Name+" "+a.Plant!.ScientificName+" "+a.Plant.Family+" "+a.Plant.Genus+" "+string.Join(" ",a.Tags)+" "+string.Join(" ",a.Plant.Names.Values)).Contains(query.Text??"",StringComparison.OrdinalIgnoreCase)).Select(a=>Item(a,lang)));if(selected.HasValue)list.SelectedKey=selected.ToString();}finally{binding=false;}
    }
    private void AddSelected()
    {
        if(!selected.HasValue)throw new ArgumentException("先选择植物。");var a=PlantService.Library.Get(selected.Value);if(draft.Palette.Any(p=>p.Asset==a.Id)){PaletteList(a.Id);return;}draft.Palette=[..draft.Palette,new(){Asset=a.Id,SpacingMeters=a.Plant!.SpacingMeters}];PaletteList(a.Id);Changed();
    }
    private void RemoveSelected(){if(!Guid.TryParse(palette.SelectedKey,out var id))return;if(draft.Manual.Any(m=>m.Asset==id))throw new ArgumentException("该植物有手工补种，暂不能移出；请保留该项。");draft.Palette=draft.Palette.Where(p=>p.Asset!=id).ToArray();PaletteList();Changed();}
    private void PaletteList(Guid? choose=null)
    {
        binding=true;try{var old=choose?.ToString()??palette.SelectedKey;var assets=PlantService.Library.List().ToDictionary(a=>a.Id);var lang=PlantUiPreferences.Load().ResolvedLanguage;palette.SetItems(draft.Palette.Select(p=>assets.TryGetValue(p.Asset,out var a)?Item(a,lang):new PlantShelfItem(p.Asset,draft.Assets.GetValueOrDefault(p.Asset)?.ScientificName??"", "",draft.Assets.GetValueOrDefault(p.Asset)?.Image??"")));palette.SelectedKey=old;if(palette.SelectedKey==null&&draft.Palette.Length>0)palette.SelectedKey=draft.Palette[0].Asset.ToString();}finally{binding=false;}PaletteFields();
    }
    private void PaletteFields(){if(binding)return;var p=draft.Palette.FirstOrDefault(p=>p.Asset.ToString()==palette.SelectedKey);if(p==null)return;binding=true;try{spacing.Value=p.SpacingMeters;weight.Value=p.Weight;}finally{binding=false;}}
    private void PaletteChanged(){if(binding)return;var p=draft.Palette.FirstOrDefault(p=>p.Asset.ToString()==palette.SelectedKey);if(p==null)return;p.SpacingMeters=spacing.Value;p.Weight=weight.Value;Changed();}
    private void Changed(){if(binding||stopped)return;pending=true;changed=DateTime.UtcNow;}
    private void Pull()
    {
        draft.Name=name.Text;var s=draft.Settings;s.Density=density.Value;s.LayoutSeed=(int)layoutSeed.Value;s.SizeSeed=(int)sizeSeed.Value;s.MirrorSeed=(int)mirrorSeed.Value;s.MinScale=minimum.Value;s.MaxScale=maximum.Value;s.MinSliderLow=minimum.Low;s.MinSliderHigh=minimum.High;s.MaxSliderLow=maximum.Low;s.MaxSliderHigh=maximum.High;s.Mirror=mirror.Checked==true;s.OverrideSpacing=ignoreSpacing.Checked==true;s.EdgeDistance=edgeDistance.Value;s.EdgeStrength=edgeStrength.Value;s.EdgeCurve=curve.Select(c=>c.Value).ToArray();s.EdgeDensity=edgeDensity.Checked==true;s.EdgeSize=edgeSize.Checked==true;s.Validate();
    }
    private void Bind()
    {
        binding=true;try{var s=draft.Settings;name.Text=draft.Name;density.Value=s.Density;layoutSeed.Value=s.LayoutSeed;sizeSeed.Value=s.SizeSeed;mirrorSeed.Value=s.MirrorSeed;minimum.Set(s.MinSliderLow,s.MinSliderHigh,s.MinScale);maximum.Set(s.MaxSliderLow,s.MaxSliderHigh,s.MaxScale);mirror.Checked=s.Mirror;ignoreSpacing.Checked=s.OverrideSpacing;edgeDistance.Value=s.EdgeDistance;edgeStrength.Value=s.EdgeStrength;for(int i=0;i<5;i++)curve[i].Value=s.EdgeCurve[i];edgeDensity.Checked=s.EdgeDensity;edgeSize.Checked=s.EdgeSize;context.Text=group.HasValue?"正在编辑选中的种植对象":"新组合 · 先添加植物，再选择承载面";}finally{binding=false;}PaletteList();pending=false;boundSpec=JsonSerializer.Serialize(draft,MaterialLibrary.Json);
    }
    private void NewDraft(){group=null;draft=new();libraryExpander.Expanded=true;Bind();status.Text="新组合；原种植对象保持。";}
    private void Poll()
    {
        if(PlantGroups.Picking)return;
        if(pending&&(DateTime.UtcNow-changed).TotalSeconds>.6){pending=false;Pull();if(group.HasValue){var current=PlantGroups.Read(Doc.Objects.FindId(group.Value)!)!;draft.Individuals=current.Individuals;draft.Manual=current.Manual;PlantGroups.Update(Doc,group.Value,draft);status.Text="参数已保存，正在更新…";}}
        var chosen=Doc.Objects.GetSelectedObjects(false,false).Where(PlantGroups.IsGroup).ToArray();string signature=string.Join(";",chosen.Select(o=>o.Id));
        if(propertiesOnly&&signature!=selectionSignature){selectionSignature=signature;if(chosen.Length==1){group=chosen[0].Id;draft=PlantGroups.Read(chosen[0])!;libraryExpander.Expanded=false;Bind();}}
        if(group.HasValue){var obj=Doc.Objects.FindId(group.Value);if(obj==null){group=null;context.Text="种植对象已删除或撤销";}else if(!pending){if(obj.Attributes.GetUserString(PlantGroups.Key)!=boundSpec){draft=PlantGroups.Read(obj)!;Bind();}var state=JsonSerializer.SerializeToElement(PlantGroups.State(Doc,group.Value),MaterialLibrary.Json);status.Text=state.GetProperty("stage").GetString()??"";}}
        if(catalogJob.HasValue){var job=CatalogService.Get(catalogJob.Value);status.Text=job.Stage;if(job.Status!="running"){catalogJob=null;Refresh();}}
        if(namesJob.HasValue){var job=CatalogService.Get(namesJob.Value);if(job.Status!="running"){namesJob=null;if(job.Status=="completed"){Refresh();PaletteList();}else status.Text=job.Stage;}}
        if(!propertiesOnly&&!namesJob.HasValue&&!CatalogService.Busy)
        {
            string key=PlantService.Library.Root+"|"+catalogSignature;
            if(key!=namesAttempt){var job=CatalogService.LocalizePlants();if(job!=null){namesAttempt=key;namesJob=job.Id;}else if(!MaterialChat.Busy&&!MaterialGeneration.HasActiveWorkers)namesAttempt=key;}
        }
        if(DateTime.UtcNow.Second%3==0){var signature2=string.Join(";",PlantService.Library.List().Select(a=>$"{a.Id}:{a.Revision}:{a.CatalogRevision}"));if(signature2!=catalogSignature)Refresh();}
    }
    private Guid Carrier()
    {
        var targets=Doc.Objects.GetSelectedObjects(false,false).Where(o=>!PlantService.IsPlant(o)&&o.Geometry is Brep or Surface or Mesh).ToArray();if(targets.Length==1)return targets[0].Id;
        using var get=new GetObject();get.SetCommandPrompt("选择种植承载曲面或网格");get.GeometryFilter=Rhino.DocObjects.ObjectType.Surface|Rhino.DocObjects.ObjectType.Brep|Rhino.DocObjects.ObjectType.Mesh;get.SubObjectSelect=false;get.Get();if(get.CommandResult()!=Rhino.Commands.Result.Success)throw new OperationCanceledException("已取消选择承载面。");var obj=get.Object(0).Object();if(PlantService.IsPlant(obj))throw new ArgumentException("请选择非植物承载面。");return obj.Id;
    }
    private void Scatter()
    {
        Pull();if(draft.Palette.Length==0)AddSelected();draft.Surface=Carrier();if(group.HasValue)PlantGroups.Update(Doc,group.Value,draft);else group=PlantGroups.Create(Doc,draft);Doc.Objects.UnselectAll();Doc.Objects.Select(group.Value);Bind();status.Text="正在生成种植组合…";Doc.Views.Redraw();
    }
    private void PlacePoint()
    {
        Poll();NamedViewExportService.RequireActive(Doc);
        Pull();if(draft.Palette.Length==0)AddSelected();if(!group.HasValue){draft.Surface=Carrier();draft.Settings.Density=0;group=PlantGroups.Create(Doc,draft);Bind();}
        else PlantGroups.Update(Doc,group.Value,draft);
        var obj=Doc.Objects.FindId(group.Value)!;var spec=PlantGroups.Read(obj)!;var source=Doc.Objects.FindId(spec.Surface)??throw new ArgumentException("承载面已删除，请重新关联。");using var mesh=PlantGroups.MeshFor(source.Geometry);mesh.Transform(PlantGroups.Matrix(obj));
        Guid asset=Guid.TryParse(palette.SelectedKey,out var paletteId)?paletteId:spec.Palette[0].Asset;PlantGroups.Picking=true;
        try{while(true){using var point=new GetPoint();point.SetCommandPrompt("连续种植 · 点击承载面 · Enter / Esc 结束");point.AcceptNothing(true);point.Constrain(mesh,false);if(point.Get()!=GetResult.Point)break;PlantGroups.AddManual(Doc,group.Value,asset,point.Point());}}
        finally{PlantGroups.Picking=false;draft=PlantGroups.Read(Doc.Objects.FindId(group.Value)!)!;Bind();Doc.Objects.UnselectAll();Doc.Objects.Select(group.Value);Doc.Views.Redraw();}
    }
    public object State()=>new{document,selected,group,stopped,catalogJob,namesJob,library=PlantService.Library.Root,palette=draft.Palette,settings=draft.Settings,presentation=PlantUiPreferences.Load(),libraryShelf=list.State(),compositionShelf=palette.State(),status=status.Text};
    internal void PlaceContinuously()=>PlacePoint();
    private void Guard(Action action){if(stopped)return;try{action();}catch(Exception e){status.Text=e.Message;}}
    private void Stop(){if(stopped)return;stopped=true;poll.Stop();if(catalogJob.HasValue)CatalogService.Cancel(catalogJob.Value);if(namesJob.HasValue)CatalogService.Cancel(namesJob.Value);}
    protected override void Dispose(bool disposing){if(disposing){Stop();poll.Dispose();tools.Remove(this);}base.Dispose(disposing);}
}

public sealed class PlantCommand:Rhino.Commands.Command
{
    public override string EnglishName=>"RhinoSceneFlowPlant";
    protected override Rhino.Commands.Result RunCommand(RhinoDoc doc,Rhino.Commands.RunMode mode)
    {
        try{SceneFlowWorkspace.Open("planting");SceneFlowWorkspace.Planting!.PlaceContinuously();return Rhino.Commands.Result.Success;}
        catch(Exception ex){RhinoApp.WriteLine(ex.Message);return Rhino.Commands.Result.Failure;}
    }
}

internal sealed class PlantScaleSlider:Panel
{
    private readonly NumericStepper low=Ui.Number(.01,100,2,70),high=Ui.Number(.01,100,2,70),value=Ui.Number(.01,100,3,75);private readonly Slider slider=new(){MinValue=0,MaxValue=1000};private bool binding;
    internal event Action? Changed;internal double Value=>value.Value;internal double Low=>low.Value;internal double High=>high.Value;
    internal PlantScaleSlider(string title,double lo,double hi,double initial)
    {
        var root=Ui.Layout();root.AddRow(ToolUi.Row(new Label{Text=title},value,null));root.AddRow(slider);root.AddRow(new Expander{Header="滑块可调区间",Content=ToolUi.Row(low,new Label{Text="–"},high,null)});Content=root;Set(lo,hi,initial);
        slider.ValueChanged+=(_,_)=>{if(binding)return;binding=true;try{value.Value=Low+(High-Low)*slider.Value/1000.0;}finally{binding=false;}Changed?.Invoke();};
        value.ValueChanged+=(_,_)=>{if(binding)return;binding=true;try{slider.Value=(int)Math.Clamp((Value-Low)/(High-Low)*1000,0,1000);}finally{binding=false;}Changed?.Invoke();};
        foreach(var n in new[]{low,high})n.ValueChanged+=(_,_)=>{if(binding)return;if(High>Low)Set(Low,High,Math.Clamp(Value,Low,High));Changed?.Invoke();};
    }
    internal void Set(double lo,double hi,double val){binding=true;try{low.Value=lo;high.Value=hi;value.Value=Math.Clamp(val,lo,hi);slider.Value=(int)((value.Value-lo)/(hi-lo)*1000);}finally{binding=false;}}
}
internal sealed class PlantCurvePreview:Drawable
{
    private readonly NumericStepper[] values;
    internal PlantCurvePreview(NumericStepper[] values){this.values=values;Height=75;foreach(var v in values)v.ValueChanged+=(_,_)=>Invalidate();}
    protected override void OnPaint(PaintEventArgs e){base.OnPaint(e);var b=new RectangleF(8,6,Math.Max(1,Width-16),Height-12);e.Graphics.DrawRectangle(Colors.Gray,b);for(int i=0;i<4;i++)e.Graphics.DrawLine(Colors.ForestGreen,new PointF(b.X+b.Width*i/4,b.Bottom-(float)values[i].Value*b.Height),new PointF(b.X+b.Width*(i+1)/4,b.Bottom-(float)values[i+1].Value*b.Height));}
}
