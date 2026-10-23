using Eto.Drawing;
using Eto.Forms;
using Rhino;
using Rhino.UI;
using System.Text.Json;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public static class ExportPanelController
{
    private static readonly Dictionary<uint,ExportPanel> windows=[];
    public static ExportPanel Open(RhinoDoc doc)
    {
        NamedViewExportService.RequireActive(doc);
        if(windows.TryGetValue(doc.RuntimeSerialNumber,out var old)){old.BringToFront();return old;}
        var panel=new ExportPanel(doc);windows[doc.RuntimeSerialNumber]=panel;
        panel.Closed+=(_,_)=>windows.Remove(doc.RuntimeSerialNumber);panel.Owner=RhinoEtoApp.MainWindowForDocument(doc);panel.Show();return panel;
    }
    public static ExportPanel? Find(uint document)=>windows.GetValueOrDefault(document);
}

public sealed class ExportPanel : Form
{
    private static ExportLayerSetting[]? copiedLayers;
    private static (int Width,int Height)? copiedSize;
    private readonly uint document;
    private readonly List<ViewExportRow> rows=[];
    private readonly Dictionary<Guid,ViewCard> cards=[];
    private readonly Queue<Guid> queue=[];
    private readonly Panel body=new(),cardHost=new();
    private readonly Scrollable overview;
    private readonly TextBox folder=new();
    private readonly Label status=new(){Text="就绪"};
    private readonly TextArea log=new(){ReadOnly=true,Height=60};
    private readonly Button export=new(){Text="导出勾选视图 · PSD"},cancel=new(){Text="取消导出",Enabled=false};
    private readonly ProgressBar progress=new(){MinValue=0,MaxValue=1};
    private readonly DynamicLayout tools=new(){Spacing=new(6,6)};
    private readonly UITimer previews=new(){Interval=.04},save=new(){Interval=.4},detailTimer=new(){Interval=.2};
    private ViewDetails? detail;
    private CancellationTokenSource? cancellation;
    private bool busy,shown,documentClosed;
    public BatchReport? LastReport{get;private set;}
    public bool IsExporting=>busy;
    internal RhinoDoc Document=>RhinoDoc.FromRuntimeSerialNumber(document)??throw new InvalidOperationException("文档已关闭。");
    public IReadOnlyList<ViewExportRow> Views=>rows;
    public ExportPanel(RhinoDoc doc)
    {
        document=doc.RuntimeSerialNumber;Title="RhinoSceneFlow · 视图导出工作台";ClientSize=new(1210,880);MinimumSize=new(1160,700);Padding=new(12);
        overview=new Scrollable{Content=cardHost,ExpandContentWidth=true};body.Content=overview;folder.Text=SceneFlowPlugin.Instance.ExportDirectory;
        tools.AddRow(Ui.Button("刷新 Named Views",()=>Guard(RefreshNamedViews)),Ui.Button("刷新全部预览",()=>{foreach(var r in rows)Queue(r.Id);}),
            Ui.Button("全选",()=>Include(true)),Ui.Button("全不选",()=>Include(false)),null);
        var browse=Ui.Button("选择文件夹…",()=>{using var d=new SelectFolderDialog{Directory=folder.Text};if(d.ShowDialog(this)==DialogResult.Ok)folder.Text=d.Directory;});
        var output=new TableLayout{Spacing=new(8,6),Rows={new TableRow(new Label{Text="输出文件夹"},new TableCell(folder,true),browse)}};
        var actions=Ui.Layout();actions.AddRow(status,null,cancel,export);
        var root=Ui.Layout();root.AddRow(new Label{Text="Named Views · 每个视图独立设置画幅和 PSD 图层",Font=new Font(SystemFont.Bold,14)});
        root.AddRow(tools);root.Add(body,true,true);root.AddRow(output);root.AddRow(progress);root.AddRow(actions);root.AddRow(log);Content=root;
        export.Click+=async(_,_)=>await StartExport();cancel.Click+=(_,_)=>{cancellation?.Cancel();status.Text="正在取消…";};
        previews.Elapsed+=(_,_)=>{if(busy||queue.Count==0){previews.Stop();return;}var id=queue.Dequeue();if(cards.TryGetValue(id,out var card))Guard(card.RefreshPreview);};
        save.Elapsed+=(_,_)=>{save.Stop();Guard(()=>WorkbenchStore.Save(Document,rows));};
        detailTimer.Elapsed+=(_,_)=>{detailTimer.Stop();if(!busy&&detail is not null)Guard(detail.RefreshPreview);};
        Shown+=(_,_)=>{shown=true;foreach(var row in rows)Queue(row.Id);};
        Closing+=(_,e)=>{if(busy&&!documentClosed){cancellation?.Cancel();e.Cancel=true;status.Text="正在取消，请完成后再关闭。";}};
        Closed+=(_,_)=>
        {
            if(!documentClosed)Guard(()=>WorkbenchStore.Save(Document,rows));RhinoDoc.CloseDocument-=OnDocumentClosed;
            foreach(var t in new[]{previews,save,detailTimer}){t.Stop();t.Dispose();}
            foreach(var c in cards.Values)c.Dispose();detail?.Dispose();cancellation?.Dispose();
        };
        RhinoDoc.CloseDocument+=OnDocumentClosed;RefreshNamedViews();
    }
    private void OnDocumentClosed(object? s,DocumentEventArgs e){if(e.Document.RuntimeSerialNumber==document){documentClosed=true;cancellation?.Cancel();Close();}}
    internal void Guard(Action action){try{action();}catch(Exception ex){status.Text=ex.Message;}}
    private void Include(bool value){foreach(var row in rows){row.Included=value;cards[row.Id].Sync();}Changed(null,false);}
    public void RefreshNamedViews()
    {
        if(busy)return;CloseDetails();
        var old=rows.Count>0?rows.ToDictionary(r=>r.Id):WorkbenchStore.Load(Document).GroupBy(r=>r.Id).ToDictionary(g=>g.Key,g=>g.First());rows.Clear();
        foreach(var v in NamedViewExportService.List(Document)){var r=old.GetValueOrDefault(v.Id)??new(){Id=v.Id,Width=v.Width,Height=v.Height};r.Name=v.Name;rows.Add(r);}
        BuildCards();status.Text=rows.Count==0?"请先在 Rhino 中保存 Named Views。":$"{rows.Count} 个视图 · 双击预览进入细节调整";
    }
    private void BuildCards()
    {
        queue.Clear();var old=cards.Values.ToArray();cards.Clear();var layout=Ui.Layout();layout.Padding=new(2);
        for(int i=0;i<rows.Count;i+=2)
        {var a=new ViewCard(this,rows[i]);cards.Add(a.Row.Id,a);ViewCard? b=null;if(i+1<rows.Count){b=new(this,rows[i+1]);cards.Add(b.Row.Id,b);}layout.AddRow(a.Root,b?.Root);}
        layout.AddRow(null);cardHost.Content=layout;foreach(var c in old)c.Dispose();if(shown)foreach(var r in rows)Queue(r.Id);
    }
    internal void Changed(ViewExportRow? row,bool refresh=true)
    {
        save.Stop();save.Start();if(row is not null){row.Status="设置已更新";if(cards.TryGetValue(row.Id,out var c))c.SyncStatus();if(refresh&&(detail is null||detail.Row!=row))Queue(row.Id);}
        if(detail is not null&&detail.Row==row){detailTimer.Stop();detailTimer.Start();}
    }
    internal void Queue(Guid id){if(!queue.Contains(id))queue.Enqueue(id);if(shown&&!busy)previews.Start();}
    public void RefreshCard(Guid id){if(!busy)cards[id].RefreshPreview();}
    public void CapturePreview(Guid id,string path)
    {if(!Path.IsPathFullyQualified(path)||!path.EndsWith(".png",StringComparison.OrdinalIgnoreCase))throw new ArgumentException("请输入绝对 PNG 路径。");Directory.CreateDirectory(Path.GetDirectoryName(path)!);using var b=WorkbenchService.Preview(Document,rows.First(r=>r.Id==id),700);b.Save(path,System.Drawing.Imaging.ImageFormat.Png);}
    public void CopyLayers(Guid id){copiedLayers=rows.First(r=>r.Id==id).Layers.Select(l=>l.Copy()).ToArray();status.Text="已复制图层配置";}
    public void PasteLayers(Guid id)
    {
        if(copiedLayers is null)throw new ArgumentException("请先复制图层配置。");
        var layers=copiedLayers.Select(l=>l.Copy()).ToList();if(layers.Count>32)throw new ArgumentException("最多 32 个图层条目。");
        var r=rows.First(r=>r.Id==id);r.Layers=layers;cards[id].RebuildLayers();Changed(r,false);
    }
    public void CopySize(Guid id){var r=rows.First(r=>r.Id==id);copiedSize=(r.Width,r.Height);status.Text="已复制输出尺寸";}
    public void PasteSize(Guid id)
    {
        if(copiedSize is not {} size)throw new ArgumentException("请先复制输出尺寸。");int w=size.Width,h=size.Height;
        var r=rows.First(r=>r.Id==id);r.Width=w;r.Height=h;cards[id].Sync();Changed(r);
    }
    public void SetView(ViewExportRow setting)
    {if(busy)throw new InvalidOperationException("正在导出。");setting.Validate();int i=rows.FindIndex(r=>r.Id==setting.Id);if(i<0)throw new ArgumentException("视图不存在。");setting=setting.Copy();setting.Name=rows[i].Name;rows[i]=setting;CloseDetails();BuildCards();Changed(setting);}
    public void OpenDetails(Guid id){if(busy)return;CloseDetails();detail=new(this,rows.First(r=>r.Id==id));body.Content=detail.Root;Guard(detail.RefreshPreview);}
    public void CloseDetails(){if(detail is null)return;detailTimer.Stop();body.Content=overview;var d=detail;detail=null;d.Dispose();Queue(d.Row.Id);}
    public void SelectNamedView(Guid id)=>OpenDetails(id);
    private FileCollision Collision(string path)
    {var a=MessageBox.Show(this,$"文件已存在：\n{path}\n\n是否覆盖？选择‘否’自动添加 001、002…","PSD 文件重名",MessageBoxButtons.YesNoCancel,MessageBoxType.Question);return a==DialogResult.Yes?FileCollision.Overwrite:a==DialogResult.No?FileCollision.Number:FileCollision.Cancel;}
    private static Task<T> OnUi<T>(Func<T> action)
    {
        if(!RhinoApp.InvokeRequired){try{return Task.FromResult(action());}catch(Exception ex){return Task.FromException<T>(ex);}}
        var t=new TaskCompletionSource<T>(TaskCreationOptions.RunContinuationsAsynchronously);RhinoApp.InvokeOnUiThread(new Action(()=>{try{t.SetResult(action());}catch(Exception ex){t.SetException(ex);}}));return t.Task;
    }
    public async Task StartExport()
    {
        if(busy)return;
        try
        {
            var plan=WorkbenchService.Plan(Document,rows,folder.Text,Collision);WorkbenchStore.Save(Document,rows);SceneFlowPlugin.Instance.ExportDirectory=Path.GetFullPath(folder.Text);
            cancellation?.Dispose();cancellation=new();var token=cancellation.Token;var results=new List<BatchFileResult>();
            busy=true;tools.Enabled=body.Enabled=folder.Enabled=export.Enabled=false;cancel.Enabled=true;previews.Stop();detailTimer.Stop();progress.MaxValue=plan.Length;progress.Value=0;log.Text="";
            try
            {
                foreach(var item in plan)
                {
                    token.ThrowIfCancellationRequested();
                    var r=await OnUi(()=>{status.Text=$"正在导出 {item.View.Name} · 捕获 / 计算 / 写入";var row=rows.First(v=>v.Id==item.View.Id);row.Status="导出中…";cards[row.Id].SyncStatus();return row;});BatchFileResult result;
                    try{using var prepared=await OnUi(()=>WorkbenchService.Prepare(Document,item,token));result=await Task.Run(()=>prepared.Write(token),token);}
                    catch(OperationCanceledException){throw;}
                    catch(Exception ex){result=new(r.Id,r.Name,item.Path,false,r.Width,r.Height,0,0,ex.Message);}
                    results.Add(result);
                    await OnUi(()=>{if(documentClosed||IsDisposed)return true;r.Status=result.Ok?"已导出":"失败";cards[r.Id].SyncStatus();progress.Value=results.Count;log.Append((result.Ok?result.Path:r.Name+"："+result.Error)+Environment.NewLine,true);return true;});
                }
                LastReport=new(results.ToArray(),false);
            }
            catch(OperationCanceledException){LastReport=new(results.ToArray(),true);}
            finally
            {
                await OnUi(()=>{busy=false;if(documentClosed||IsDisposed)return true;tools.Enabled=body.Enabled=folder.Enabled=export.Enabled=true;cancel.Enabled=false;
                    foreach(var r in rows.Where(r=>r.Status=="导出中…")){r.Status="已取消";cards[r.Id].SyncStatus();}
                    status.Text=$"{(LastReport?.Cancelled==true?"已取消":"完成")} · 成功 {results.Count(r=>r.Ok)} / 失败 {results.Count(r=>!r.Ok)}";if(queue.Count>0)previews.Start();return true;});
            }
        }
        catch(OperationCanceledException){status.Text="已取消，未写入文件。";}
        catch(Exception ex){if(!IsDisposed)status.Text=ex.Message;}
    }
    public object GetState()=>new{document,busy,visible=Visible,directory=folder.Text,status=status.Text,detail=detail?.Row.Id,views=rows.ToArray(),
        previews=cards.Values.Select(c=>new{id=c.Row.Id,loaded=c.Loaded}).ToArray(),displayModes=WorkbenchService.Modes().Select(m=>new{id=m.Id,name=m.LocalName}).ToArray(),lastReport=LastReport};
}

internal static class Ui
{
    internal static readonly (string Key,string Name)[] Blends=[("norm","正常"),("mul ","正片叠底"),("scrn","滤色"),("over","叠加"),("dark","变暗"),("lite","变亮")];
    internal static DynamicLayout Layout()=>new(){Spacing=new(8,8)};
    internal static Button Button(string text,Action click,int width=-1){var b=new Button{Text=text};if(width>0)b.Width=width;b.Click+=(_,_)=>click();return b;}
    internal static NumericStepper Number(double min,double max,int decimals=0,int width=82)=>new(){MinValue=min,MaxValue=max,DecimalPlaces=decimals,Width=width};
    internal static DropDown Modes(Guid selected){var d=new DropDown{Width=220};foreach(var m in WorkbenchService.Modes())d.Items.Add(new ListItem{Key=m.Id.ToString(),Text=m.LocalName});d.SelectedKey=selected.ToString();return d;}
    internal static Bitmap Bitmap(System.Drawing.Bitmap b){using var s=new MemoryStream();b.Save(s,System.Drawing.Imaging.ImageFormat.Png);s.Position=0;return new Bitmap(s);}
    internal static void Picture(ImageView image,PixelLayout frame,System.Drawing.Bitmap b,int w,int h)
    {double scale=Math.Min((double)w/b.Width,(double)h/b.Height);var old=image.Image;image.Image=Bitmap(b);old?.Dispose();var size=new Size(Math.Max(1,(int)Math.Round(b.Width*scale)),Math.Max(1,(int)Math.Round(b.Height*scale)));image.Size=size;frame.Move(image,(w-size.Width)/2,(h-size.Height)/2);}
}

internal sealed class ViewCard : IDisposable
{
    private readonly ExportPanel owner;
    internal ViewExportRow Row{get;}
    internal GroupBox Root{get;}
    private readonly ImageView image=new();
    private readonly PixelLayout frame=new(){Size=new(506,230),BackgroundColor=Color.FromArgb(30,34,39)};
    private readonly CheckBox included=new(){Text="导出此视图"};
    private readonly Label status=new();
    private readonly NumericStepper width=Ui.Number(64,8192),height=Ui.Number(64,8192);
    private readonly DropDown modes,presets=new(){Width=82};
    private readonly Panel layerHost=new();
    private bool binding;
    internal bool Loaded{get;private set;}
    internal ViewCard(ExportPanel owner,ViewExportRow row)
    {
        this.owner=owner;Row=row;modes=Ui.Modes(row.Mode);frame.Add(image,0,0);image.MouseDoubleClick+=(_,_)=>owner.OpenDetails(row.Id);frame.MouseDoubleClick+=(_,_)=>owner.OpenDetails(row.Id);
        foreach(var p in new[]{("0","自定义"),("1024","1K"),("2048","2K"),("4096","4K"),("8192","8K")})presets.Items.Add(new ListItem{Key=p.Item1,Text=p.Item2});
        included.CheckedChanged+=(_,_)=>{if(!binding){row.Included=included.Checked==true;owner.Changed(row,false);}};
        width.ValueChanged+=(_,_)=>SizeChanged();height.ValueChanged+=(_,_)=>SizeChanged();
        presets.SelectedValueChanged+=(_,_)=>{if(binding||!int.TryParse(presets.SelectedKey,out int n)||n==0)return;row.SetPreset(n);Sync();owner.Changed(row);};
        modes.SelectedValueChanged+=(_,_)=>{if(!binding&&Guid.TryParse(modes.SelectedKey,out var id)){row.Mode=id;owner.Changed(row);}};
        var header=Ui.Layout();header.AddRow(included,null,status,Ui.Button("细节调整",()=>owner.OpenDetails(row.Id)));
        var previewTools=Ui.Layout();previewTools.AddRow(new Label{Text="预览"},modes,null,Ui.Button("刷新",()=>owner.Guard(RefreshPreview)));
        var size=Ui.Layout();size.Spacing=new(4,4);size.AddRow(new Label{Text="像素"},width,new Label{Text="×"},height,presets,Ui.Button("复制",()=>owner.Guard(()=>owner.CopySize(row.Id))),Ui.Button("粘贴",()=>owner.Guard(()=>owner.PasteSize(row.Id))));
        var layers=Ui.Layout();layers.AddRow(new Label{Text="PSD 图层 · 从上到下",Font=new Font(SystemFont.Bold,10)},null,Ui.Button("复制配置",()=>owner.Guard(()=>owner.CopyLayers(row.Id))),Ui.Button("粘贴",()=>owner.Guard(()=>owner.PasteLayers(row.Id))));
        var content=Ui.Layout();content.Padding=new(10);content.AddRow(header);content.AddRow(frame);content.AddRow(previewTools);content.AddRow(size);content.AddRow(layers);
        content.AddRow(new Label{Text="内容 / 混合模式 / 不透明度（%）· ↑↓ 调整顺序"});content.AddRow(layerHost);
        content.AddRow(Ui.Button("＋ 添加图层",()=>{row.Layers.Add(new());RebuildLayers();owner.Changed(row,false);}),null);
        Root=new GroupBox{Text=row.Name,Width=544,Content=content};Sync();RebuildLayers();
    }
    private void SizeChanged(){if(binding)return;Row.Width=(int)width.Value;Row.Height=(int)height.Value;owner.Changed(Row);}
    internal void Sync(){binding=true;try{included.Checked=Row.Included;width.Value=Row.Width;height.Value=Row.Height;modes.SelectedKey=Row.Mode.ToString();presets.SelectedKey="0";SyncStatus();}finally{binding=false;}}
    internal void SyncStatus()=>status.Text=Row.Status;
    internal void RebuildLayers()
    {
        var layout=Ui.Layout();layout.Spacing=new(3,5);
        for(int index=0;index<Row.Layers.Count;index++)
        {
            int i=index;var l=Row.Layers[i];var enabled=new CheckBox{Checked=l.Enabled};var type=new DropDown{Width=160};
            type.Items.Add(new ListItem{Key="",Text="请选择通道 / 显示模式…"});type.Items.Add(new ListItem{Key="shadow",Text="通道 · 阴影"});type.Items.Add(new ListItem{Key="material",Text="通道 · 材质 / 图层色"});
            foreach(var m in WorkbenchService.Modes())type.Items.Add(new ListItem{Key="display:"+m.Id,Text="模式 · "+m.LocalName});type.SelectedKey=l.Kind=="display"?"display:"+l.Mode:l.Kind;
            var blend=new DropDown{Width=96};foreach(var b in Ui.Blends)blend.Items.Add(new ListItem{Key=b.Key,Text=b.Name});blend.SelectedKey=l.Blend;
            var opacity=Ui.Number(0,100,0,55);opacity.Value=l.Opacity;
            type.SelectedValueChanged+=(_,_)=>{var key=type.SelectedKey??"";l.Kind=key.StartsWith("display:",StringComparison.Ordinal)?"display":key;l.Mode=l.Kind=="display"?Guid.Parse(key[8..]):Guid.Empty;owner.Changed(Row,false);};
            enabled.CheckedChanged+=(_,_)=>{l.Enabled=enabled.Checked==true;owner.Changed(Row,false);};blend.SelectedValueChanged+=(_,_)=>{l.Blend=blend.SelectedKey??"norm";owner.Changed(Row,false);};opacity.ValueChanged+=(_,_)=>{l.Opacity=(int)opacity.Value;owner.Changed(Row,false);};
            var up=Ui.Button("↑",()=>Move(i,-1),25);up.Enabled=i>0;var down=Ui.Button("↓",()=>Move(i,1),25);down.Enabled=i+1<Row.Layers.Count;
            layout.AddRow(enabled,type,blend,opacity,new Label{Text="%"},up,down,Ui.Button("×",()=>{Row.Layers.RemoveAt(i);RebuildLayers();owner.Changed(Row,false);},25));
        }
        layerHost.Content=layout;
    }
    private void Move(int i,int d){(Row.Layers[i],Row.Layers[i+d])=(Row.Layers[i+d],Row.Layers[i]);RebuildLayers();owner.Changed(Row,false);}
    internal void RefreshPreview(){using var b=WorkbenchService.Preview(owner.Document,Row,506);Ui.Picture(image,frame,b,506,230);Loaded=true;}
    public void Dispose(){image.Image?.Dispose();Root.Dispose();}
}

internal sealed class ViewDetails : IDisposable
{
    private readonly ExportPanel owner;
    internal ViewExportRow Row{get;}
    internal Scrollable Root{get;}
    private readonly ImageView image=new();
    private readonly PixelLayout frame=new(){Size=new(1050,430),BackgroundColor=Color.FromArgb(30,34,39)};
    private readonly NumericStepper yaw=Ui.Number(-180,180,1),pitch=Ui.Number(-89,89,1),zoom=Ui.Number(.01,100,2),panX=Ui.Number(-1e9,1e9,3),panY=Ui.Number(-1e9,1e9,3),panZ=Ui.Number(-1e9,1e9,3),azimuth=Ui.Number(0,360,1),altitude=Ui.Number(.1,90,1);
    private readonly CheckBox documentSun=new(){Text="使用文档太阳"};
    private bool binding;private PointF? drag;
    internal ViewDetails(ExportPanel owner,ViewExportRow row)
    {
        this.owner=owner;Row=row;frame.Add(image,0,0);
        image.MouseDown+=(_,e)=>{if(e.Buttons.HasFlag(MouseButtons.Primary))drag=e.Location;};image.MouseUp+=(_,_)=>drag=null;
        image.MouseMove+=(_,e)=>{if(drag is not {} p||!e.Buttons.HasFlag(MouseButtons.Primary))return;row.Camera.Yaw=Math.Clamp(row.Camera.Yaw+(e.Location.X-p.X)*.35,-180,180);row.Camera.Pitch=Math.Clamp(row.Camera.Pitch+(e.Location.Y-p.Y)*.35,-89,89);drag=e.Location;Sync();owner.Changed(row);};
        image.MouseWheel+=(_,e)=>{row.Camera.Zoom=Math.Clamp(row.Camera.Zoom*Math.Pow(1.1,Math.Sign(e.Delta.Height)),.01,100);Sync();owner.Changed(row);};
        foreach(var n in new[]{yaw,pitch,zoom,panX,panY,panZ,azimuth,altitude})n.ValueChanged+=(_,_)=>Apply();documentSun.CheckedChanged+=(_,_)=>Apply();
        var mode=Ui.Modes(row.Mode);mode.SelectedValueChanged+=(_,_)=>{if(Guid.TryParse(mode.SelectedKey,out var id)){row.Mode=id;owner.Changed(row);}};
        var top=Ui.Layout();top.AddRow(Ui.Button("← 返回全部视图",owner.CloseDetails),new Label{Text=row.Name,Font=new Font(SystemFont.Bold,13)},null,mode,Ui.Button("刷新预览",()=>owner.Guard(RefreshPreview)));
        var camera=Ui.Layout();camera.AddRow(new Label{Text="水平旋转 °"},yaw,new Label{Text="俯仰 °"},pitch,new Label{Text="缩放"},zoom,null);
        camera.AddRow(new Label{Text="目标平移 X"},panX,new Label{Text="Y"},panY,new Label{Text="Z"},panZ,null);
        camera.AddRow(Ui.Button("重置相机",()=>{row.Camera=new();Sync();owner.Changed(row);}),Ui.Button("写回 Named View 相机",()=>owner.Guard(()=>{WorkbenchService.WriteBack(owner.Document,row);owner.CloseDetails();owner.RefreshNamedViews();owner.Changed(row);})),null);
        var sun=Ui.Layout();sun.AddRow(documentSun,new Label{Text="太阳方位 °"},azimuth,new Label{Text="高度 °"},altitude,null);
        var content=Ui.Layout();content.Padding=new(6);content.AddRow(top);content.AddRow(frame);
        content.AddRow(new Label{Text="拖动旋转，滚轮缩放。相机 / 太阳只用于此视图导出；写回按钮只更新 Named View 相机。"});content.AddRow(camera);content.AddRow(sun);
        content.AddRow(new Label{Text="太阳设置同时用于显示模式和独立阴影通道；独立阴影不包含反射 / GI / AO。"});content.AddRow(null);Root=new Scrollable{Content=content,ExpandContentWidth=true};Sync();
    }
    private void Sync(){binding=true;try{var c=Row.Camera;yaw.Value=c.Yaw;pitch.Value=c.Pitch;zoom.Value=c.Zoom;panX.Value=c.PanX;panY.Value=c.PanY;panZ.Value=c.PanZ;documentSun.Checked=Row.Sun.UseDocument;azimuth.Value=Row.Sun.Azimuth;altitude.Value=Row.Sun.Altitude;azimuth.Enabled=altitude.Enabled=!Row.Sun.UseDocument;}finally{binding=false;}}
    private void Apply(){if(binding)return;var c=Row.Camera;c.Yaw=yaw.Value;c.Pitch=pitch.Value;c.Zoom=zoom.Value;c.PanX=panX.Value;c.PanY=panY.Value;c.PanZ=panZ.Value;Row.Sun.UseDocument=documentSun.Checked==true;Row.Sun.Azimuth=azimuth.Value;Row.Sun.Altitude=altitude.Value;azimuth.Enabled=altitude.Enabled=!Row.Sun.UseDocument;owner.Changed(Row);}
    internal void RefreshPreview(){using var b=WorkbenchService.Preview(owner.Document,Row,1050);Ui.Picture(image,frame,b,1050,430);}
    public void Dispose(){image.Image?.Dispose();Root.Dispose();}
}
