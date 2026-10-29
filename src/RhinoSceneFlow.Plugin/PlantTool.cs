using Eto.Forms;
using Rhino;
using Rhino.Geometry;
using Rhino.Input;
using Rhino.Input.Custom;
using RhinoSceneFlow.Core;
namespace RhinoSceneFlow.Plugin;

public sealed class PlantTool:Panel
{
    private static readonly HashSet<PlantTool> tools=[];
    private readonly uint document;
    private readonly TextBox query=new(){PlaceholderText="搜索名称、学名或标签"};
    private readonly DropDown family=new(),genus=new(),tag=new(),mode=new();
    private readonly ListBox list=new(){Height=160};
    private readonly ImageView preview=new();private readonly PixelLayout frame=new(){Size=new(280,180)};
    private readonly Label description=new(){Wrap=WrapMode.Word,Width=270},status=new(){Wrap=WrapMode.Word,Width=270};
    private readonly NumericStepper height=Ui.Number(.01,150,2,90),min=Ui.Number(.05,20,2,85),max=Ui.Number(.05,20,2,85),seed=Ui.Number(int.MinValue,int.MaxValue,0,110),count=Ui.Number(1,10000,0,90),spacing=Ui.Number(0,1000,2,90),angle=Ui.Number(10,85,0,85);
    private readonly CheckBox mirror=new(){Text="随机水平镜像",Checked=true};
    private readonly UITimer poll=new(){Interval=2};
    private Guid? selected,catalogJob;private bool stopped,refreshing;private string signature="";
    private RhinoDoc Doc=>RhinoDoc.FromRuntimeSerialNumber(document)??throw new InvalidOperationException("文档已关闭。");
    internal static void StopDocument(uint serial){foreach(var t in tools.Where(t=>t.document==serial).ToArray())t.Stop();}
    public PlantTool(RhinoDoc doc)
    {
        document=doc.RuntimeSerialNumber;tools.Add(this);frame.Add(preview,0,0);min.Value=.85;max.Value=1.15;seed.Value=42;count.Value=20;spacing.Value=1;angle.Value=PlantService.Settings.Angle;
        foreach(var (key,text) in new[]{("auto","自动朝向"),("z","只绕 Z 轴"),("free","完全朝向相机")})mode.Items.Add(new ListItem{Key=key,Text=text});mode.SelectedKey=PlantService.Settings.Mode;
        var root=Ui.Layout();root.AddRow(ToolUi.Heading("植物库 · 种植"));root.AddRow(Ui.Button("在现有 AI 聊天中生成植物",()=>SceneFlowWorkspace.Open("materials")));
        root.AddRow(ToolUi.Row(Ui.Button("刷新",()=>Guard(Refresh)),Ui.Button("AI 整理植物库",()=>Guard(()=>{catalogJob=CatalogService.Organize(true).Id;})),null));
        var body=Ui.Layout();body.AddRow(query);body.AddRow(family);body.AddRow(genus);body.AddRow(tag);body.AddRow(list);body.AddRow(frame);body.AddRow(description);
        body.AddRow(ToolUi.Row(new Label{Text="参考高度 m"},height,null));body.AddRow(new Label{Text="高度为可调整的素材参考值。以基部落地，不改变原图。",Width=270,Wrap=WrapMode.Word});
        var settings=Ui.Layout();settings.AddRow(ToolUi.Row(new Label{Text="随机缩放"},min,new Label{Text="–"},max,null));settings.AddRow(mirror);settings.AddRow(ToolUi.Row(new Label{Text="种子"},seed,null));settings.AddRow(ToolUi.Row(new Label{Text="散布数量"},count,null));settings.AddRow(ToolUi.Row(new Label{Text="最小间距 m"},spacing,null));
        settings.AddRow(mode);settings.AddRow(ToolUi.Row(new Label{Text="自动切换角度 °"},angle,null));settings.AddRow(Ui.Button("保存全局朝向",()=>Guard(()=>{PlantService.Settings=new(){Mode=mode.SelectedKey??"auto",Angle=angle.Value};status.Text="全局朝向已保存；各视口独立计算。";})));
        body.AddRow(new Expander{Header="随机与全局朝向",Content=settings});root.Add(new Scrollable{Content=body,ExpandContentWidth=true},true,true);root.AddRow(Ui.Button("点选种植",()=>Guard(PlacePoint)));root.AddRow(Ui.Button("在当前选中曲面／网格散布",()=>Guard(Scatter)));root.AddRow(status);
        Content=root;query.TextChanged+=(_,_)=>Filter();family.SelectedValueChanged+=(_,_)=>Filter();genus.SelectedValueChanged+=(_,_)=>Filter();tag.SelectedValueChanged+=(_,_)=>Filter();list.SelectedIndexChanged+=(_,_)=>{if(!refreshing&&list.SelectedKey is string key)Guard(()=>Select(Guid.Parse(key)));};
        Refresh();poll.Elapsed+=(_,_)=>Guard(()=>
        {
            if(catalogJob.HasValue){var job=CatalogService.Get(catalogJob.Value);status.Text=job.Stage;if(job.Status!="running"){catalogJob=null;Refresh();}}
            var current=string.Join(";",PlantService.Library.List().Select(a=>$"{a.Id}:{a.Revision}:{a.CatalogRevision}"));if(current!=signature)Refresh();
        });poll.Start();
    }
    public void Select(Guid id)
    {
        var a=PlantService.Library.Get(id);if(a.Plant==null)throw new ArgumentException("不是植物素材。");selected=id;PlantService.Selected[document]=id;height.Value=a.HeightMeters;
        description.Text=a.Name+"\n"+a.Plant.ScientificName+(a.Plant.Cultivar.Length>0?" '"+a.Plant.Cultivar+"'":"")+"\n"+a.Plant.Family+" / "+a.Plant.Genus+"\n"+string.Join(" · ",a.Tags);
        using var image=new System.Drawing.Bitmap(PlantService.Library.MapPath(a,"baseColor"));Ui.Picture(preview,frame,image,280,180);
        refreshing=true;try{list.SelectedKey=id.ToString();}finally{refreshing=false;}
    }
    public void Refresh()
    {
        if(stopped)return;var assets=PlantService.Library.List();signature=string.Join(";",assets.Select(a=>$"{a.Id}:{a.Revision}:{a.CatalogRevision}"));
        refreshing=true;
        try
        {
            if(selected.HasValue&&!assets.Any(a=>a.Id==selected.Value)){selected=null;PlantService.Selected.Remove(document);var old=preview.Image;preview.Image=null;old?.Dispose();description.Text="在当前植物库中选择素材。";}
            string? f=family.SelectedKey,t=tag.SelectedKey,g=genus.SelectedKey;family.Items.Clear();genus.Items.Clear();tag.Items.Clear();family.Items.Add(new ListItem{Key="",Text="所有科"});genus.Items.Add(new ListItem{Key="",Text="所有属"});tag.Items.Add(new ListItem{Key="",Text="所有标签"});
            foreach(var s in assets.Select(a=>a.Plant!.Family).Distinct().Order())family.Items.Add(new ListItem{Key=s,Text=s});
            foreach(var s in assets.Select(a=>a.Plant!.Genus).Distinct().Order())genus.Items.Add(new ListItem{Key=s,Text=s});genus.SelectedKey=g??"";
            foreach(var s in assets.SelectMany(a=>a.Tags).Distinct().Order())tag.Items.Add(new ListItem{Key=s,Text=s});family.SelectedKey=f??"";tag.SelectedKey=t??"";
        }
        finally{refreshing=false;}Filter();
        if(selected==null&&PlantService.Selected.TryGetValue(document,out var id)&&assets.Any(a=>a.Id==id))Select(id);
    }
    private void Filter()
    {
        if(stopped||refreshing)return;Guard(()=>
        {
            refreshing=true;try{list.Items.Clear();foreach(var a in PlantService.Library.List().Where(a=>(family.SelectedKey is null or ""||a.Plant!.Family==family.SelectedKey)&&(genus.SelectedKey is null or ""||a.Plant!.Genus==genus.SelectedKey)&&(tag.SelectedKey is null or ""||a.Tags.Contains(tag.SelectedKey))&&(a.Name+" "+a.Plant!.ScientificName+" "+string.Join(" ",a.Tags)).Contains(query.Text??"",StringComparison.OrdinalIgnoreCase)))list.Items.Add(new ListItem{Key=a.Id.ToString(),Text=a.Name+" · "+a.Plant!.ScientificName});if(selected.HasValue)list.SelectedKey=selected.ToString();}finally{refreshing=false;}
        });
    }
    private Guid Asset()
    {
        if(!selected.HasValue)throw new ArgumentException("先生成或选择植物。");var a=PlantService.Library.Get(selected.Value);if(Math.Abs(a.HeightMeters-height.Value)>1e-8){a.WidthMeters*=height.Value/a.HeightMeters;a.HeightMeters=height.Value;PlantService.Library.Update(a);}return selected.Value;
    }
    private void PlacePoint()
    {
        var id=Asset();NamedViewExportService.RequireActive(Doc);using var point=new GetPoint();point.SetCommandPrompt("选择植物基部位置");if(point.Get()!=GetResult.Point)return;
        PlantService.Place(Doc,id,[point.Point()],(int)seed.Value,min.Value,max.Value,mirror.Checked==true);status.Text="已种植；可移动锚点调整位置。";
    }
    private void Scatter()
    {
        var id=Asset();var targets=ToolUi.Selection(Doc);if(targets.Length!=1)throw new ArgumentException("先选择一个作为种植区域的曲面或网格。");
        var result=PlantService.Scatter(Doc,id,targets[0],(int)count.Value,spacing.Value,(int)seed.Value,min.Value,max.Value,mirror.Checked==true);status.Text=System.Text.Json.JsonSerializer.Serialize(result,MaterialLibrary.Json);
    }
    public object State()=>new{document,selected,stopped,catalogJob,library=PlantService.Library.Root,settings=PlantService.Settings,count=list.Items.Count,status=status.Text};
    private void Guard(Action action){if(stopped)return;try{action();}catch(Exception e){status.Text=e.Message;}}
    private void Stop(){if(stopped)return;stopped=true;poll.Stop();if(catalogJob.HasValue)CatalogService.Cancel(catalogJob.Value);}
    protected override void Dispose(bool disposing){if(disposing){Stop();poll.Dispose();tools.Remove(this);var image=preview.Image;preview.Image=null;image?.Dispose();}base.Dispose(disposing);}
}
