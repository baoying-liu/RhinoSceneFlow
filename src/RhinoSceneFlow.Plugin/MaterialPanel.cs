using Eto.Drawing;
using Eto.Forms;
using Rhino;
using Rhino.Commands;
using RhinoEtoApp=Rhino.UI.RhinoEtoApp;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class MaterialLibraryCommand : Rhino.Commands.Command
{
    public override string EnglishName=>"RhinoSceneFlowMaterialLibrary";
    protected override Result RunCommand(RhinoDoc doc,RunMode mode)
    {try{MaterialPanelController.Open(doc);return Result.Success;}catch(Exception e){RhinoApp.WriteLine(e.Message);return Result.Failure;}}
}
public static class MaterialPanelController
{
    private static readonly Dictionary<uint,MaterialPanel> windows=[];
    public static MaterialPanel Open(RhinoDoc doc)
    {
        NamedViewExportService.RequireActive(doc);if(windows.TryGetValue(doc.RuntimeSerialNumber,out var old)){old.BringToFront();return old;}
        var p=new MaterialPanel(doc);windows.Add(doc.RuntimeSerialNumber,p);p.Closed+=(_,_)=>windows.Remove(doc.RuntimeSerialNumber);p.Owner=RhinoEtoApp.MainWindowForDocument(doc);p.Show();return p;
    }
    public static MaterialPanel? Find(uint serial)=>windows.GetValueOrDefault(serial);
}
public sealed class MaterialPanel : Form
{
    private const int PreviewWidth=320,PreviewHeight=200;
    private readonly uint document;
    private readonly ListBox list=new(){Width=245};
    private readonly TextBox search=new(){PlaceholderText="名称 / 分类 / 标签"},name=new(){Text="新材质"},category=new(),tags=new();
    private readonly NumericStepper width=Ui.Number(.001,1e8,2,110),height=Ui.Number(.001,1e8,2,110),roughness=Ui.Number(0,1,2),metallic=Ui.Number(0,1,2);
    private readonly Dictionary<string,TextBox> maps=MaterialLibrary.Slots.ToDictionary(k=>k,_=>new TextBox());
    private readonly ImageView image=new(){Size=new(PreviewWidth,PreviewHeight)};
    private readonly CheckBox repeat=new(){Text="3×3 重复预览",Checked=true};
    private readonly Label physical=new(),status=new(){Text="就绪",Wrap=WrapMode.Word,Width=980},directory=new(){Wrap=WrapMode.Word,Width=850};
    private readonly DropDown mode=new(){Width=160},axis=new(){Width=100},alignment=new(){Width=170},target=new(){Width=150},layer=new(){Width=280};
    private readonly NumericStepper rotation=Ui.Number(-360,360,1),offsetU=Ui.Number(-1e12,1e12,2),offsetV=Ui.Number(-1e12,1e12,2);
    private readonly NumericStepper originX=Ui.Number(-1e12,1e12,2),originY=Ui.Number(-1e12,1e12,2),originZ=Ui.Number(-1e12,1e12,2);
    private readonly TextArea prompt=new(){Height=65,Wrap=true};
    private readonly Label generation=new(){Text="使用本机 Codex 登录生成图片，完成后自动入库。也可直接导入图片。",Wrap=WrapMode.Word};
    private readonly UITimer poll=new(){Interval=2};
    private MaterialAsset[] assets=[];
    private Guid? selected,lastJob;
    private bool binding;
    private RhinoDoc Doc=>RhinoDoc.FromRuntimeSerialNumber(document)??throw new InvalidOperationException("文档已关闭。");
    public MaterialPanel(RhinoDoc doc)
    {
        document=doc.RuntimeSerialNumber;Title="RhinoSceneFlow · 真实尺寸材质库";ClientSize=new(1110,900);MinimumSize=new(1050,740);Padding=new(12);
        width.Value=height.Value=1000;roughness.Value=.65;
        name.Width=category.Width=tags.Width=220;foreach(var box in maps.Values)box.Width=175;prompt.Width=700;generation.Width=700;
        Fill(mode,[("auto","自动选择"),("plane","平面"),("box","箱式 / 分面投影"),("cylinder","圆柱侧面")]);
        Fill(axis,[("auto","自动"),("x","X"),("y","Y"),("z","Z")]);Fill(alignment,[("continuous","连续铺贴 / 共用原点"),("object","以每个物件为起点")]);
        Fill(target,[("objects","当前选中对象"),("layer","指定图层现有对象")]);RefreshLayers();
        var left=Ui.Layout();left.Width=245;left.AddRow(new Label{Text="材质库",Font=new Font(SystemFont.Bold,14)});left.AddRow(search);left.Add(list,true,true);
        left.AddRow(Row(Ui.Button("刷新",RefreshLibrary),Ui.Button("新建 / 清空",New),null));
        var edit=Ui.Layout();edit.Width=380;edit.AddRow(new Label{Text="整张贴图代表的物理尺寸",Font=new Font(SystemFont.Bold,12)});
        edit.AddRow(Row(Field("名称"),name));edit.AddRow(Row(Field("分类"),category));edit.AddRow(Row(Field("标签（逗号分隔）"),tags));
        edit.AddRow(Row(Field("宽 × 高（mm）"),width,new Label{Text="×"},height));
        edit.AddRow(Row(Field("粗糙度 / 金属度"),roughness,metallic));
        foreach(var slot in MaterialLibrary.Slots)
        {var key=slot;edit.AddRow(Row(Field(slot=="baseColor"?"Base Color *":slot),maps[slot],Ui.Button("选择…",()=>ChooseImage(key),56)));}
        edit.AddRow(Row(Ui.Button("导入为新材质",ImportCurrent),Ui.Button("保存尺寸 / 参数",SaveCurrent),null));
        edit.AddRow(Row(Ui.Button("导出材质包…",ExportPackage),Ui.Button("导入材质包…",ImportPackage),null));
        var preview=Ui.Layout();preview.Width=320;preview.AddRow(image);preview.AddRow(repeat);preview.AddRow(physical);preview.AddRow(new Label{Text="棋盘整张对应此处宽高；重复预览用于检查接缝。",Wrap=WrapMode.Word,Width=320});
        var upper=Ui.Layout();upper.AddRow(edit,preview);
        var mapping=Ui.Layout();mapping.AddRow(new Label{Text="赋材质与映射",Font=new Font(SystemFont.Bold,12)});
        mapping.AddRow(Row(new Label{Text="目标"},target,layer,Ui.Button("刷新图层",RefreshLayers),null));
        mapping.AddRow(Row(new Label{Text="映射"},mode,new Label{Text="轴向"},axis,alignment,null));
        mapping.AddRow(Row(new Label{Text="旋转 °"},rotation,new Label{Text="偏移 U / V（mm）"},offsetU,offsetV,null));
        mapping.AddRow(Row(new Label{Text="平面 / 箱式原点（mm）"},originX,originY,originZ,null));
        mapping.AddRow(Row(Ui.Button("检查应用范围",()=>Apply(false,true)),Ui.Button("应用尺寸棋盘格",()=>Apply(true,false)),Ui.Button("应用材质",()=>Apply(false,false)),null));
        mapping.AddRow(Row(Ui.Button("重新映射 / 同步尺寸",Remap),Ui.Button("恢复应用前材质与映射",Restore),null));
        mapping.AddRow(new Label{Text="移动 / 缩放、改变单位、图层新增物件后，请重新映射或再次应用。块实例暂不支持。",Wrap=WrapMode.Word,Width=700});
        var ai=Ui.Layout();ai.AddRow(new Label{Text="AI 生成描述",Font=new Font(SystemFont.Bold,12)});ai.AddRow(prompt);ai.AddRow(Row(Ui.Button("生成材质",RequestGeneration),Ui.Button("取消等待任务",CancelGeneration),null));ai.AddRow(generation);
        var right=Ui.Layout();right.Width=730;right.AddRow(upper);right.AddRow(mapping);right.AddRow(ai);right.AddRow(null);
        var content=Ui.Layout();content.AddRow(left,new Scrollable{Content=right,ExpandContentWidth=true});
        var root=Ui.Layout();root.Add(content,true,true);root.AddRow(Row(directory,Ui.Button("切换材质库…",ChangeLibrary),null));root.AddRow(status);Content=root;
        search.TextChanged+=(_,_)=>Guard(RefreshLibrary);list.SelectedValueChanged+=(_,_)=>{if(!binding&&Guid.TryParse(list.SelectedKey,out var id))Guard(()=>Select(id));};
        repeat.CheckedChanged+=(_,_)=>Guard(RefreshImage);width.ValueChanged+=(_,_)=>{UpdateSizeLabel();if(!binding)Guard(RefreshImage);};height.ValueChanged+=(_,_)=>{UpdateSizeLabel();if(!binding)Guard(RefreshImage);};
        poll.Elapsed+=(_,_)=>Guard(PollGeneration);poll.Start();
        RhinoDoc.CloseDocument+=OnDocumentClosed;Closed+=(_,_)=>{RhinoDoc.CloseDocument-=OnDocumentClosed;poll.Stop();poll.Dispose();var old=image.Image;image.Image=null;old?.Dispose();};
        RefreshLibrary();UpdateSizeLabel();
    }
    private void OnDocumentClosed(object? sender,DocumentEventArgs e){if(e.Document.RuntimeSerialNumber==document)Close();}
    private void Guard(Action action){try{action();}catch(Exception ex){status.Text=ex.Message;}}
    private static Label Field(string text)=>new(){Text=text,Width=120};
    private static TableLayout Row(params Control?[] controls)=>new(){Spacing=new(6,4),Rows={new TableRow(controls.Select(c=>new TableCell(c,c==null)).ToArray())}};
    private static void Fill(DropDown drop,(string Key,string Label)[] items){foreach(var i in items)drop.Items.Add(new ListItem{Key=i.Key,Text=i.Label});drop.SelectedIndex=0;}
    public void RefreshLibrary()
    {
        binding=true;try{assets=MaterialService.Library.List(search.Text);list.Items.Clear();foreach(var a in assets)list.Items.Add(new ListItem{Key=a.Id.ToString(),Text=a.Name});if(selected.HasValue)list.SelectedKey=selected.ToString();directory.Text=MaterialService.Library.Root;}finally{binding=false;}
    }
    private void RefreshLayers(){string? key=layer.SelectedKey;layer.Items.Clear();foreach(var l in Doc.Layers.Where(l=>!l.IsDeleted&&!l.IsReference))layer.Items.Add(new ListItem{Key=l.Id.ToString(),Text=l.FullPath});if(key!=null)layer.SelectedKey=key;if(layer.SelectedIndex<0&&layer.Items.Count>0)layer.SelectedIndex=0;}
    public void Select(Guid id)
    {
        var a=MaterialService.Library.Get(id);selected=id;binding=true;
        try{name.Text=a.Name;category.Text=a.Category;tags.Text=string.Join(", ",a.Tags);width.Value=a.WidthMeters*1000;height.Value=a.HeightMeters*1000;roughness.Value=a.Roughness;metallic.Value=a.Metallic;mode.SelectedKey=a.RecommendedMapping;
            foreach(var slot in MaterialLibrary.Slots)maps[slot].Text=a.Maps.ContainsKey(slot)?MaterialService.Library.MapPath(a,slot):"";list.SelectedKey=id.ToString();}
        finally{binding=false;}RefreshImage();
    }
    private MaterialAsset Descriptor()=>new(){Id=selected??Guid.NewGuid(),Name=name.Text,Category=category.Text,Tags=tags.Text.Split([',','，'],StringSplitOptions.RemoveEmptyEntries|StringSplitOptions.TrimEntries),WidthMeters=width.Value/1000,HeightMeters=height.Value/1000,Roughness=roughness.Value,Metallic=metallic.Value,RecommendedMapping=mode.SelectedKey??"auto"};
    private void New(){selected=null;list.SelectedIndex=-1;name.Text="新材质";category.Text=tags.Text="";foreach(var box in maps.Values)box.Text="";RefreshImage();}
    private void ChooseImage(string slot)=>Guard(()=>{using var d=new OpenFileDialog();d.Filters.Add(new FileFilter("贴图",".png",".jpg",".jpeg"));if(d.ShowDialog(this)==DialogResult.Ok){maps[slot].Text=d.FileName;if(slot=="baseColor")RefreshImage();}});
    private void ImportCurrent()=>Guard(()=>{var files=maps.Where(p=>!string.IsNullOrWhiteSpace(p.Value.Text)).ToDictionary(p=>p.Key,p=>p.Value.Text);var a=MaterialService.Import(Descriptor(),files);RefreshLibrary();Select(a.Id);status.Text="已入库；图像已复制到材质库，使用相对路径。";});
    private void SaveCurrent()=>Guard(()=>{if(selected==null)throw new ArgumentException("请先导入材质。");var a=MaterialService.Library.Update(Descriptor());RefreshLibrary();Select(a.Id);status.Text="参数已保存；已有物件请重新映射 / 应用以同步。";});
    private MappingSettings Mapping(bool checker)=>new(){Mode=mode.SelectedKey??"auto",Axis=axis.SelectedKey??"auto",Alignment=alignment.SelectedKey??"continuous",Rotation=rotation.Value,OffsetUMeters=offsetU.Value/1000,OffsetVMeters=offsetV.Value/1000,OriginMeters=[originX.Value/1000,originY.Value/1000,originZ.Value/1000],Checker=checker};
    private (Guid[]? Objects,Guid[]? Layers) Target()
    {
        if(target.SelectedKey=="layer")return(null,[Guid.Parse(layer.SelectedKey??throw new ArgumentException("请选择图层。"))]);
        return(Doc.Objects.GetSelectedObjects(false,false).Select(o=>o.Id).ToArray(),null);
    }
    private void Apply(bool checker,bool preview)=>Guard(()=>
    {
        if(selected==null)throw new ArgumentException("请先选择已入库材质。");
        var a=MaterialService.Library.Get(selected.Value);var draft=Descriptor();
        if(a.WidthMeters!=draft.WidthMeters||a.HeightMeters!=draft.HeightMeters||a.Roughness!=draft.Roughness||a.Metallic!=draft.Metallic||a.Name!=draft.Name||a.Category!=draft.Category||!a.Tags.SequenceEqual(draft.Tags))throw new ArgumentException("材质尺寸或参数尚未保存，请先点击“保存尺寸 / 参数”。");
        var t=Target();var result=MaterialService.Apply(Doc,selected.Value,t.Objects,t.Layers,Mapping(checker),preview);
        if(preview){using var json=System.Text.Json.JsonDocument.Parse(MaterialService.Serialize(result));var r=json.RootElement;status.Text=$"将处理 {r.GetProperty("objects").GetArrayLength()} 个对象；贴图 {r.GetProperty("widthInModelUnits").GetDouble():G6} × {r.GetProperty("heightInModelUnits").GetDouble():G6} {r.GetProperty("unit").GetString()}，原映射会备份。";}
        else status.Text=checker?"已应用尺寸棋盘格，可用应用材质替换。":"已按真实尺寸应用材质。";
    });
    private void Remap()=>Guard(()=>{var t=Target();if(t.Layers!=null)MaterialService.SyncLayers(Doc,t.Layers);else MaterialService.Remap(Doc,t.Objects!);status.Text="已重新按真实尺寸映射。";});
    private void Restore()=>Guard(()=>{var t=Target();MaterialService.Restore(Doc,t.Objects,t.Layers);status.Text="已恢复原材质与映射。";});
    private void ExportPackage()=>Guard(()=>{if(selected==null)throw new ArgumentException("请选择材质。");using var d=new SaveFileDialog();d.Filters.Add(new FileFilter("材质包",".zip"));d.FileName=name.Text+".zip";if(d.ShowDialog(this)==DialogResult.Ok){MaterialService.Library.ExportPackage(selected.Value,d.FileName);status.Text="材质包已导出。";}});
    private void ImportPackage()=>Guard(()=>{using var d=new OpenFileDialog();d.Filters.Add(new FileFilter("材质包",".zip"));if(d.ShowDialog(this)==DialogResult.Ok){var a=MaterialService.Library.ImportPackage(d.FileName,MaterialService.ValidateImages);RefreshLibrary();Select(a.Id);}});
    private void ChangeLibrary()=>Guard(()=>{using var d=new SelectFolderDialog{Directory=MaterialService.Library.Root};if(d.ShowDialog(this)==DialogResult.Ok){SceneFlowPlugin.Instance.MaterialDirectory=d.Directory;selected=null;lastJob=null;RefreshLibrary();New();}});
    private void RequestGeneration()=>Guard(()=>{if(lastJob.HasValue&&MaterialGeneration.Get(lastJob.Value).Status is "pending" or "running")throw new ArgumentException("已有等待中的 AI 任务，请先完成或取消。");var job=MaterialGeneration.Start(Descriptor(),prompt.Text);lastJob=job.Id;generation.Text="正在启动本机 Codex · "+job.Id;});
    private void CancelGeneration()=>Guard(()=>{if(lastJob==null)throw new ArgumentException("没有正在等待的任务。");MaterialGeneration.Cancel(lastJob.Value);generation.Text="任务已取消。";lastJob=null;});
    private void PollGeneration()
    {
        if(lastJob==null)return;var job=MaterialGeneration.Get(lastJob.Value);
        generation.Text=job.Stage;
        if(job.Status=="failed"){lastJob=null;return;}
        if(job.Status=="completed"&&job.Material.HasValue){RefreshLibrary();Select(job.Material.Value);generation.Text="AI 材质已生成并入库，请检查接缝与物理尺寸。";lastJob=null;}
        else if(job.Status=="cancelled"){generation.Text="任务已取消。";lastJob=null;}
    }
    private void UpdateSizeLabel()=>physical.Text=$"整张：{width.Value:G6} × {height.Value:G6} mm";
    private void RefreshImage()
    {
        string path=maps["baseColor"].Text;var old=image.Image;image.Image=null;old?.Dispose();if(!File.Exists(path))return;
        using var source=new System.Drawing.Bitmap(path);using var preview=new System.Drawing.Bitmap(PreviewWidth,PreviewHeight);using var g=System.Drawing.Graphics.FromImage(preview);g.Clear(System.Drawing.Color.FromArgb(235,235,235));
        int n=repeat.Checked==true?3:1;double ratio=width.Value/height.Value;int tw=Math.Max(1,(int)Math.Min((double)PreviewWidth/n,(double)PreviewHeight/n*ratio)),th=Math.Max(1,(int)(tw/ratio));
        int ox=(PreviewWidth-tw*n)/2,oy=(PreviewHeight-th*n)/2;
        for(int y=0;y<n;y++)for(int x=0;x<n;x++)g.DrawImage(source,new System.Drawing.Rectangle(ox+x*tw,oy+y*th,tw,th));
        image.Image=Ui.Bitmap(preview);UpdateSizeLabel();
    }
    public object GetState()=>new{open=true,document,library=MaterialService.Library.Root,selected,assets=assets.Select(a=>new{a.Id,a.Name,a.WidthMeters,a.HeightMeters}).ToArray(),lastJob,status=status.Text};
}
