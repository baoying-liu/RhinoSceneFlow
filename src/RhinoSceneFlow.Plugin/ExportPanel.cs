using Eto.Drawing;
using Eto.Forms;
using Rhino;
using Rhino.UI;
using System.Text.Json;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public static class ExportPanelController
{
    public static ExportPanel Open(RhinoDoc doc)
    {
        NamedViewExportService.RequireActive(doc);SceneFlowWorkspace.Open("export");
        return SceneFlowWorkspace.Export??throw new InvalidOperationException("导出面板未初始化。");
    }
    public static ExportPanel? Find(uint document)=>SceneFlowWorkspace.Export is {} p&&p.Document.RuntimeSerialNumber==document?p:null;
}

public sealed class ExportPanel : Panel
{
    private static ExportLayerSetting[]? copiedLayers;
    private static (bool Include,bool Separate) copiedPlantShadowOptions;
    private static (int Width,int Height)? copiedSize;
    private readonly uint document;
    private readonly List<ViewExportRow> rows=[];
    private readonly Dictionary<Guid,ViewCard> cards=[];
    private readonly Queue<Guid> queue=[];
    private readonly Panel body=new(),cardHost=new();
    private readonly Scrollable overview;
    private readonly UiTextBox folder=new();
    private readonly UiLabel status=new(){Text="就绪"};
    private readonly TextArea log=new(){ReadOnly=true,Height=60};
    private readonly UiButton export=new(){Text="导出勾选视图 · PSD",MinimumSize=new(0,28)},cancel=new(){Text="取消导出",Enabled=false,Visible=false};
    private readonly ProgressBar progress=new(){MinValue=0,MaxValue=1,Visible=false};
    private readonly DynamicLayout tools=new(){Spacing=new(6,6)};
    private readonly UITimer previews=new(){Interval=.04},save=new(){Interval=.4},detailTimer=new(){Interval=.2};
    private readonly UITimer namedViews=new(){Interval=1};
    private ViewDetails? detail;
    private CancellationTokenSource? cancellation;
    private bool busy,shown,documentClosed,closed;
    internal bool ClosedForUpdates=>closed;
    public BatchReport? LastReport{get;private set;}
    public bool IsExporting=>busy;
    internal RhinoDoc Document=>RhinoDoc.FromRuntimeSerialNumber(document)??throw new InvalidOperationException("文档已关闭。");
    public IReadOnlyList<ViewExportRow> Views=>rows;
    public ExportPanel(RhinoDoc doc)
    {
        document=doc.RuntimeSerialNumber;Padding=new(2);
        overview=ToolUi.VerticalScroll(cardHost);body.Content=overview;folder.Text=SceneFlowPlugin.Instance.ExportDirectory;
        tools.AddRow(ToolUi.Pair(Ui.Button("展开全部画面设置",()=>SetExpansion(true,"view")),Ui.Button("折叠全部画面设置",()=>SetExpansion(false,"view"))));
        tools.AddRow(ToolUi.Row(Ui.Button("全选",()=>Include(true)),Ui.Button("全不选",()=>Include(false)),null));
        var newView=new Panel{Visible=false};var newName=new UiTextBox{PlaceholderText="留空自动命名"};
        void Create(){Guard(()=>{WorkbenchService.CreateNamedView(Document,string.IsNullOrWhiteSpace(newName.Text)?null:newName.Text);newView.Visible=false;newName.Text="";});}
        newName.KeyDown+=(_,e)=>{if(e.KeyData==Keys.Enter){e.Handled=true;Create();}else if(e.KeyData==Keys.Escape){e.Handled=true;newView.Visible=false;}};
        var create=Ui.Layout();create.AddRow(ToolUi.Note("将当前 Rhino 视口保存为已命名视图"));create.AddRow(newName);create.AddRow(ToolUi.Pair(Ui.Button("创建视图",Create),Ui.Button("取消",()=>newView.Visible=false)));newView.Content=create;
        var add=Ui.Button("＋",()=>{if(busy)return;newView.Visible=!newView.Visible;if(newView.Visible)newName.Focus();},28);add.ToolTip="从当前视口创建已命名视图";
        var refresh=Ui.Button("↻",()=>Guard(RefreshNamedViews),28);refresh.ToolTip="刷新全部已命名视图与预览";
        var browse=Ui.Button("选择文件夹…",()=>{using var d=new SelectFolderDialog{Directory=folder.Text};if(d.ShowDialog(this)==DialogResult.Ok)folder.Text=d.Directory;});
        var output=Ui.Layout();output.AddRow(folder);output.AddRow(browse);
        var actions=Ui.Layout();actions.AddRow(status);actions.AddRow(cancel);actions.AddRow(export);
        var root=Ui.Layout();root.AddRow(new TableLayout{Spacing=new(6,0),Rows={new TableRow(new TableCell(ToolUi.Heading("PSD · 视图导出"),true),add,refresh)}});
        root.AddRow(newView);root.AddRow(tools);root.Add(body,true,true);root.AddRow(ToolUi.Section("输出文件夹",output));root.AddRow(progress);root.AddRow(actions);root.AddRow(new UiExpander{Header="导出日志",Content=log});Content=root;
        export.Click+=async(_,_)=>await StartExport();cancel.Click+=(_,_)=>{cancellation?.Cancel();status.Text="正在取消…";};
        previews.Elapsed+=(_,_)=>{if(closed)return;if(busy||queue.Count==0){previews.Stop();return;}var id=queue.Dequeue();if(cards.TryGetValue(id,out var card))Guard(card.RefreshPreview);};
        save.Elapsed+=(_,_)=>{if(closed)return;save.Stop();Guard(()=>WorkbenchStore.Save(Document,rows));};
        detailTimer.Elapsed+=(_,_)=>{if(closed)return;detailTimer.Stop();if(!busy&&detail is not null)Guard(detail.RefreshPreview);};
        Load+=(_,_)=>{if(closed)return;shown=true;foreach(var row in rows)Queue(row.Id);};
        namedViews.Elapsed+=(_,_)=>Guard(SyncNamedViews);namedViews.Start();RhinoDoc.CloseDocument+=OnDocumentClosed;RefreshNamedViews();
    }
    protected override void Dispose(bool disposing)
    {
        if(disposing&&!closed)
        {
            closed=true;shown=false;cancellation?.Cancel();queue.Clear();
            // Form.Close does not imply IsDisposed; child disposal can fire value
            // events and already queued timer ticks can still reach this window.
            if(!documentClosed)try{WorkbenchStore.Save(Document,rows);}catch(Exception ex){RhinoApp.WriteLine(ex.Message);}
            RhinoDoc.CloseDocument-=OnDocumentClosed;
            foreach(var t in new[]{previews,save,detailTimer,namedViews}){t.Stop();t.Dispose();}
            // Clear logical rows and detach card/detail roots while parents live.
            var root=Content;Content=null;if(root is DynamicLayout layout)layout.Clear();cardHost.Content=null;body.Content=null;
            foreach(var c in cards.Values)c.Dispose();detail?.Dispose();cancellation?.Dispose();
            root?.Dispose();
        }
        base.Dispose(disposing);
    }
    private void OnDocumentClosed(object? s,DocumentEventArgs e){if(!closed&&e.Document.RuntimeSerialNumber==document){documentClosed=true;cancellation?.Cancel();previews.Stop();save.Stop();detailTimer.Stop();namedViews.Stop();}}
    internal void PresentationChanged(){if(closed||documentClosed)return;save.Stop();save.Start();}
    public void SetExpansion(bool value,string scope,Guid? id=null)
    {
        if(busy)throw new InvalidOperationException("正在导出。");if(scope is not ("view" or "layers"))throw new ArgumentException("scope: view | layers");
        foreach(var c in cards.Values.Where(c=>id==null||c.Row.Id==id)){if(scope=="view")c.SetSettingsExpanded(value);else c.SetLayersExpanded(value);}
    }
    public void RenameView(Guid id,string name){WorkbenchService.RenameNamedView(Document,id,name);var row=rows.First(r=>r.Id==id);using var view=WorkbenchService.Find(Document,id);row.Name=view.Name;cards[id].UpdateName();PresentationChanged();}
    private void SyncNamedViews()
    {
        if(closed||documentClosed||busy||RhinoApp.InCommand>0||cards.Values.Any(c=>c.EditingName))return;
        var current=NamedViewExportService.List(Document);
        if(!current.Select(v=>v.Id).SequenceEqual(rows.Select(v=>v.Id))){RefreshNamedViews();return;}
        bool changed=false;foreach(var v in current){var r=rows.First(r=>r.Id==v.Id);if(r.Name==v.Name)continue;r.Name=v.Name;cards[r.Id].UpdateName();changed=true;}if(changed)PresentationChanged();
    }
    internal void Guard(Action action){if(closed||IsDisposed)return;try{action();}catch(Exception ex){if(!closed&&!IsDisposed)status.Text=ex.Message;}}
    private void Include(bool value){foreach(var row in rows){row.Included=value;cards[row.Id].Sync();}Changed(null,false);}
    public void RefreshNamedViews()
    {
        if(busy)return;CloseDetails();
        var old=rows.Count>0?rows.ToDictionary(r=>r.Id):WorkbenchStore.Load(Document).GroupBy(r=>r.Id).ToDictionary(g=>g.Key,g=>g.First());rows.Clear();
        foreach(var v in NamedViewExportService.List(Document)){var r=old.GetValueOrDefault(v.Id)??new(){Id=v.Id,Width=v.Width,Height=v.Height};r.Name=v.Name;r.InitializePlants();rows.Add(r);}
        BuildCards();status.Text=rows.Count==0?"请先在 Rhino 中保存 Named Views。":$"{rows.Count} 个视图 · 双击预览进入细节调整";
    }
    private void BuildCards()
    {
        queue.Clear();var old=cards.Values.ToArray();cards.Clear();var layout=Ui.Layout();layout.Padding=new(2);
        foreach(var row in rows){var card=new ViewCard(this,row);cards.Add(row.Id,card);layout.AddRow(card.Root);}
        layout.AddRow(null);cardHost.Content=layout;foreach(var c in old)c.Dispose();if(shown)foreach(var r in rows)Queue(r.Id);
    }
    internal void Changed(ViewExportRow? row,bool refresh=true)
    {
        if(closed||IsDisposed)return;
        save.Stop();save.Start();if(row is not null){row.Status="设置已更新";if(cards.TryGetValue(row.Id,out var c))c.SyncStatus();if(refresh&&(detail is null||detail.Row!=row))Queue(row.Id);}
        if(detail is not null&&detail.Row==row){detailTimer.Stop();detailTimer.Start();}
    }
    internal void Queue(Guid id){if(closed||IsDisposed)return;if(!queue.Contains(id))queue.Enqueue(id);if(shown&&!busy)previews.Start();}
    public void RefreshCard(Guid id){if(!busy)cards[id].RefreshPreview();}
    public void CapturePreview(Guid id,string path)
    {if(!Path.IsPathFullyQualified(path)||!path.EndsWith(".png",StringComparison.OrdinalIgnoreCase))throw new ArgumentException("请输入绝对 PNG 路径。");Directory.CreateDirectory(Path.GetDirectoryName(path)!);using var b=WorkbenchService.Preview(Document,rows.First(r=>r.Id==id),700);b.Save(path,System.Drawing.Imaging.ImageFormat.Png);}
    public void CopyLayers(Guid id){var row=rows.First(r=>r.Id==id);copiedLayers=row.Layers.Select(l=>l.Copy()).ToArray();copiedPlantShadowOptions=(row.PlantShadows,row.SeparatePlantShadows);status.Text="已复制图层配置";}
    public void PasteLayers(Guid id)
    {
        if(copiedLayers is null)throw new ArgumentException("请先复制图层配置。");
        var layers=copiedLayers.Select(l=>l.Copy()).ToList();if(layers.Count>32)throw new ArgumentException("最多 32 个图层条目。");
        var r=rows.First(r=>r.Id==id);r.Layers=layers;r.PlantShadows=copiedPlantShadowOptions.Include;r.SeparatePlantShadows=copiedPlantShadowOptions.Separate;cards[id].RebuildLayers();Changed(r,false);
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
        if(busy||closed||IsDisposed)return;
        try
        {
            var plan=WorkbenchService.Plan(Document,rows,folder.Text,Collision);WorkbenchStore.Save(Document,rows);SceneFlowPlugin.Instance.ExportDirectory=Path.GetFullPath(folder.Text);
            cancellation?.Dispose();cancellation=new();var token=cancellation.Token;var results=new List<BatchFileResult>();
            busy=true;tools.Enabled=body.Enabled=folder.Enabled=export.Enabled=false;cancel.Enabled=cancel.Visible=progress.Visible=true;previews.Stop();detailTimer.Stop();progress.MaxValue=plan.Length;progress.Value=0;log.Text="";
            try
            {
                foreach(var item in plan)
                {
                    token.ThrowIfCancellationRequested();
                    var r=await OnUi(()=>{token.ThrowIfCancellationRequested();if(closed||documentClosed)throw new OperationCanceledException(token);status.Text=$"正在导出 {item.View.Name} · 捕获 / 计算 / 写入";var row=rows.First(v=>v.Id==item.View.Id);row.Status="导出中…";cards[row.Id].SyncStatus();return row;});BatchFileResult result;
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
                await OnUi(()=>{busy=false;if(documentClosed||IsDisposed)return true;tools.Enabled=body.Enabled=folder.Enabled=export.Enabled=true;cancel.Enabled=cancel.Visible=progress.Visible=false;
                    foreach(var r in rows.Where(r=>r.Status=="导出中…")){r.Status="已取消";cards[r.Id].SyncStatus();}
                    status.Text=$"{(LastReport?.Cancelled==true?"已取消":"完成")} · 成功 {results.Count(r=>r.Ok)} / 失败 {results.Count(r=>!r.Ok)}";if(queue.Count>0)previews.Start();return true;});
            }
        }
        catch(OperationCanceledException){if(!closed&&!IsDisposed)status.Text="已取消，未写入文件。";}
        catch(Exception ex){if(!closed&&!IsDisposed)status.Text=ex.Message;}
    }
    public object GetState()=>new{document,busy,visible=Visible,directory=folder.Text,status=status.Text,detail=detail?.Row.Id,views=rows.ToArray(),
        previews=cards.Values.Select(c=>new{id=c.Row.Id,loaded=c.Loaded}).ToArray(),displayModes=WorkbenchService.Modes().Select(m=>new{id=m.Id,name=m.LocalName}).ToArray(),lastReport=LastReport};
}

internal static class Ui
{
    internal static readonly (string Key,string Name)[] Blends=[("norm","正常"),("mul ","正片叠底"),("scrn","滤色"),("over","叠加"),("dark","变暗"),("lite","变亮")];
    internal static DynamicLayout Layout()=>new(){Spacing=new(8,8)};
    internal static UiButton Button(string text,Action click,int width=-1){var b=new UiButton{Text=text,MinimumSize=new(0,26)};if(width>0)b.Width=width;b.Click+=(_,_)=>click();return b;}
    internal static NumericStepper Number(double min,double max,int decimals=0,int width=82)=>new(){MinValue=min,MaxValue=max,DecimalPlaces=decimals,Width=width};
    internal static DropDown Modes(Guid selected){var d=new DropDown{Width=100,Tag="display-modes"};foreach(var m in WorkbenchService.Modes())d.Items.Add(new UiListItem{Key=m.Id.ToString(),IsUserContent=false,Text=m.EnglishName});d.SelectedKey=selected.ToString();return d;}
    internal static void FitPicture(ImageView image,PixelLayout frame)
    {
        if(image.IsDisposed||image.Image is not {} bitmap)return;
        double scale=Math.Min((double)Math.Max(1,frame.Width)/bitmap.Width,(double)Math.Max(1,frame.Height)/bitmap.Height);
        var size=new Size(Math.Max(1,(int)Math.Round(bitmap.Width*scale)),Math.Max(1,(int)Math.Round(bitmap.Height*scale)));
        image.Size=size;frame.Move(image,(frame.Width-size.Width)/2,(frame.Height-size.Height)/2);
    }
    internal static Bitmap Bitmap(System.Drawing.Bitmap b){using var s=new MemoryStream();b.Save(s,System.Drawing.Imaging.ImageFormat.Png);s.Position=0;return new Bitmap(s);}
    internal static void Picture(ImageView image,PixelLayout frame,System.Drawing.Bitmap b,int w,int h)
    {double scale=Math.Min((double)w/b.Width,(double)h/b.Height);var old=image.Image;image.Image=Bitmap(b);old?.Dispose();var size=new Size(Math.Max(1,(int)Math.Round(b.Width*scale)),Math.Max(1,(int)Math.Round(b.Height*scale)));image.Size=size;frame.Move(image,(w-size.Width)/2,(h-size.Height)/2);}
}

internal sealed class ViewCard : IDisposable
{
    private readonly ExportPanel owner;
    internal ViewExportRow Row{get;}
    internal UiGroupBox Root{get;}
    private readonly ImageView image=new();
    private readonly PixelLayout frame=new(){Size=new(160,150),BackgroundColor=Color.FromArgb(30,34,39)};
    private readonly UiCheckBox included=new(){Text="导出此视图"};
    private readonly UiLabel status=new(){Wrap=WrapMode.Word},nameLabel=ToolUi.Heading(""),nameError=new(){Wrap=WrapMode.Word,Visible=false};
    private readonly UiTextBox nameEdit=new();private readonly Panel nameHost=new();
    private readonly NumericStepper width=Ui.Number(64,8192),height=Ui.Number(64,8192);
    private readonly DropDown modes,presets=new(){Width=82};
    private readonly Panel layerHost=new();
    private readonly UiExpander sizeSection,layersSection,seasonSection;
    private readonly List<UiExpander> layerSections=[];
    private bool binding,closed,rebuilding;
    private bool EventsActive=>!closed&&!rebuilding&&!owner.ClosedForUpdates;
    internal bool EditingName{get;private set;}
    internal bool Loaded{get;private set;}
    internal ViewCard(ExportPanel owner,ViewExportRow row)
    {
        this.owner=owner;Row=row;modes=Ui.Modes(row.Mode);modes.Width=100;frame.Add(image,0,0);frame.SizeChanged+=(_,_)=>Ui.FitPicture(image,frame);
        image.MouseDoubleClick+=(_,e)=>{e.Handled=true;owner.Guard(()=>WorkbenchService.Activate(owner.Document,row));};frame.MouseDoubleClick+=(_,e)=>{e.Handled=true;owner.Guard(()=>WorkbenchService.Activate(owner.Document,row));};
        nameLabel.Text=row.Name;nameLabel.Tag="user-content";nameLabel.ToolTip="双击修改名称，同步 Rhino 已命名视图";nameHost.Content=nameLabel;
        nameLabel.MouseDoubleClick+=(_,_)=>BeginRename();nameEdit.LostFocus+=(_,_)=>CommitRename();nameEdit.KeyDown+=(_,e)=>{if(e.KeyData==Keys.Enter){e.Handled=true;CommitRename();}else if(e.KeyData==Keys.Escape){e.Handled=true;CancelRename();}};
        foreach(var p in new[]{("0","自定义"),("1024","1K"),("2048","2K"),("4096","4K"),("8192","8K")})presets.Items.Add(new UiListItem{Key=p.Item1,Text=p.Item2});
        included.CheckedChanged+=(_,_)=>{if(!binding&&!closed){row.Included=included.Checked==true;owner.Changed(row,false);}};
        width.ValueChanged+=(_,_)=>SizeChanged();height.ValueChanged+=(_,_)=>SizeChanged();
        presets.SelectedValueChanged+=(_,_)=>{if(binding||closed||!int.TryParse(presets.SelectedKey,out int n)||n==0)return;row.SetPreset(n);Sync();owner.Changed(row);};
        modes.SelectedValueChanged+=(_,_)=>{if(!binding&&!closed&&Guid.TryParse(modes.SelectedKey,out var id)){row.Mode=id;owner.Changed(row);}};
        var size=Ui.Layout();size.AddRow(ToolUi.Row(width,new UiLabel{Text="×"},height,null));size.AddRow(presets);
        size.AddRow(ToolUi.Row(new UiLabel{Text="预览"},modes,null,Ui.Button("↻",()=>owner.Guard(RefreshPreview),28)));
        sizeSection=new(){Header=SectionHeader("页面大小",()=>owner.CopySize(row.Id),()=>owner.PasteSize(row.Id)),Content=size,Expanded=row.SizeExpanded};
        sizeSection.ExpandedChanged+=(_,_)=>{if(closed)return;row.SizeExpanded=sizeSection.Expanded;owner.PresentationChanged();};
        var layers=Ui.Layout();layers.AddRow(ToolUi.Pair(Ui.Button("展开所有图层",()=>SetLayersExpanded(true)),Ui.Button("折叠所有图层",()=>SetLayersExpanded(false))));
        layers.AddRow(ToolUi.Note("从上到下排序 · 眼睛控制 PSD 显示 · 勾选控制是否导出"));layers.AddRow(layerHost);
        layers.AddRow(Ui.Button("＋ 添加图层",()=>{row.Layers.Add(new());RebuildLayers();owner.Changed(row,false);}));
        layersSection=new(){Header=SectionHeader("PSD 图层",()=>owner.CopyLayers(row.Id),()=>owner.PasteLayers(row.Id)),Content=layers,Expanded=row.LayerSettingsExpanded};
        layersSection.ExpandedChanged+=(_,_)=>{if(closed)return;row.LayerSettingsExpanded=layersSection.Expanded;owner.PresentationChanged();};
        var seasons=new DropDown{Width=100};foreach(string s in Seasons.All)seasons.Items.Add(new UiListItem{Key=s,Text=Seasons.Name(s)+"季"});seasons.SelectedKey=row.PreviewSeason;
        var follow=new UiCheckBox{Text="跟随预览导出",Checked=row.FollowPreviewSeason};var checks=Seasons.All.Select(s=>new UiCheckBox{Text=Seasons.Name(s),Tag=s,Checked=row.ExportSeasons.Contains(s),Enabled=!row.FollowPreviewSeason}).ToArray();
        seasons.SelectedValueChanged+=(_,_)=>{if(!EventsActive)return;row.PreviewSeason=seasons.SelectedKey!;owner.Changed(row);};
        follow.CheckedChanged+=(_,_)=>{if(!EventsActive)return;row.FollowPreviewSeason=follow.Checked==true;foreach(var c in checks)c.Enabled=!row.FollowPreviewSeason;owner.Changed(row,false);};
        foreach(var c in checks)c.CheckedChanged+=(_,_)=>{if(!EventsActive)return;row.ExportSeasons=checks.Where(x=>x.Checked==true).Select(x=>(string)x.Tag).ToArray();owner.Changed(row,false);};
        var seasonal=Ui.Layout();seasonal.AddRow(ToolUi.Row(ToolUi.Note("预览季节"),seasons,null));seasonal.AddRow(follow);seasonal.AddRow(ToolUi.Row(checks.Cast<Control>().ToArray()));seasonal.AddRow(ToolUi.Note("默认夏季；相同素材版本合并输出，文件名包含季节。缺失版本使用夏季。"));
        seasonSection=new(){Header="季节",Content=seasonal,Expanded=row.SeasonExpanded};seasonSection.ExpandedChanged+=(_,_)=>{if(!EventsActive)return;row.SeasonExpanded=seasonSection.Expanded;owner.PresentationChanged();};
        var content=Ui.Layout();content.Padding=new(8);content.AddRow(nameHost);content.AddRow(nameError);content.AddRow(ToolUi.Pair(included,Ui.Button("细节调整",()=>owner.OpenDetails(row.Id))));content.AddRow(frame);content.AddRow(sizeSection);content.AddRow(seasonSection);content.AddRow(layersSection);content.AddRow(status);
        Root=new UiGroupBox{Content=content};Sync();RebuildLayers();
    }
    private Control SectionHeader(string title,Action copy,Action paste)
    {
        var c=Ui.Button("复制",()=>owner.Guard(copy),42);c.ToolTip="复制"+title+"设置";
        var p=Ui.Button("粘贴",()=>owner.Guard(paste),42);p.ToolTip="粘贴"+title+"设置";
        return new TableLayout{Spacing=new(4,0),Rows={new TableRow(new TableCell(ToolUi.Note(title),true),c,p)}};
    }
    internal void SetSettingsExpanded(bool value){sizeSection.Expanded=value;seasonSection.Expanded=value;layersSection.Expanded=value;}
    internal void SetLayersExpanded(bool value){foreach(var section in layerSections)section.Expanded=value;}
    internal void UpdateName(){if(!EditingName)nameLabel.Text=Row.Name;}
    private void BeginRename(){if(closed||owner.IsExporting)return;EditingName=true;nameEdit.Text=Row.Name;nameHost.Content=nameEdit;nameError.Visible=false;nameEdit.Focus();nameEdit.SelectAll();}
    private void CancelRename(){EditingName=false;nameError.Visible=false;nameHost.Content=nameLabel;nameLabel.Text=Row.Name;}
    private void CommitRename()
    {
        if(closed||owner.ClosedForUpdates||!EditingName)return;
        try{owner.RenameView(Row.Id,nameEdit.Text);CancelRename();}
        catch(Exception e){nameError.Text=e.Message;nameError.Visible=true;}
    }
    private void SizeChanged(){if(binding||!EventsActive)return;Row.Width=(int)width.Value;Row.Height=(int)height.Value;owner.Changed(Row);}
    private static readonly Bitmap shownEye=EyeIcon(true),hiddenEye=EyeIcon(false);
    private static Bitmap EyeIcon(bool visible)
    {
        var bitmap=new Bitmap(24,20,PixelFormat.Format32bppRgba);using var g=new Graphics(bitmap);g.Clear(Colors.Transparent);var color=Color.FromArgb(130,160,150);g.DrawEllipse(color,2,5,20,10);g.FillEllipse(color,9,7,6,6);if(!visible){g.DrawLine(new Pen(color,2),3,2,21,18);}return bitmap;
    }
    internal void Sync(){binding=true;try{included.Checked=Row.Included;width.Value=Row.Width;height.Value=Row.Height;modes.SelectedKey=Row.Mode.ToString();presets.SelectedKey="0";UpdateName();SyncStatus();}finally{binding=false;}}
    internal void SyncStatus()=>status.Text=Row.Status;
    private string Title(ExportLayerSetting l)=>l.Kind switch{"plants"=>"植物","shadow"=>"阴影","texture"=>"材质贴图","material"=>"图层颜色（旧版）","color"=>"材质颜色","depth"=>"深度图","display"=>WorkbenchService.Modes().FirstOrDefault(m=>m.Id==l.Mode)?.LocalName??"显示模式",_=>"选择图层内容"};
    internal void RebuildLayers()
    {
        if(owner.ClosedForUpdates||closed)return;rebuilding=true;try{layerSections.Clear();var layout=Ui.Layout();layout.Spacing=new(4,6);
        for(int index=0;index<Row.Layers.Count;index++)
        {
            int i=index;var l=Row.Layers[i];var enabled=new UiCheckBox{Checked=l.Enabled,ToolTip="是否导出此图层"};
            var eye=Ui.Button("",()=>{},28);eye.Image=l.Visible?shownEye:hiddenEye;eye.ToolTip=l.Visible?"PSD 中可见；点击隐藏":"PSD 中隐藏；点击显示";
            eye.Click+=(_,_)=>{if(!EventsActive||eye.IsDisposed)return;l.Visible=!l.Visible;eye.Image=l.Visible?shownEye:hiddenEye;eye.ToolTip=l.Visible?"PSD 中可见；点击隐藏":"PSD 中隐藏；点击显示";owner.Changed(Row,false);};
            var up=Ui.Button("↑",()=>Move(i,-1),24);up.Enabled=i>0;up.ToolTip="上移图层";
            var down=Ui.Button("↓",()=>Move(i,1),24);down.Enabled=i+1<Row.Layers.Count;down.ToolTip="下移图层";
            var remove=Ui.Button("×",()=>{Row.Layers.RemoveAt(i);RebuildLayers();owner.Changed(Row,false);},24);remove.ToolTip="移除此图层配置";
            var title=ToolUi.Note(Title(l));// Separate channel identity from actions: text-only labels must also
            // fit narrow docks, and icon mode must not consume the title space.
            var identity=new TableLayout{Spacing=new(3,0),Rows={new TableRow(eye,enabled,new TableCell(title,true))}};
            var actions=ToolUi.Row(up,down,remove,null);
            var head=new TableLayout{Spacing=new(0,3),Rows={new TableRow(identity),new TableRow(actions)}};
            var type=new DropDown{Width=100};type.Items.Add(new UiListItem{Key="",Text="请选择通道 / 显示模式…"});
            foreach(var (key,text) in new[]{("plants","通道 · 植物"),("shadow","通道 · 阴影"),("texture","通道 · 材质贴图"),("color","通道 · 材质颜色"),("depth","通道 · 深度图"),("material","旧版 · 图层颜色")})type.Items.Add(new UiListItem{Key=key,Text=text});
            foreach(var m in WorkbenchService.Modes())type.Items.Add(new UiListItem{Key="display:"+m.Id,Text="模式 · "+m.EnglishName});type.SelectedKey=l.Kind=="display"?"display:"+l.Mode:l.Kind;
            var detail=Ui.Layout();detail.AddRow(type);
            var blend=new DropDown{Width=96};foreach(var b in Ui.Blends)blend.Items.Add(new UiListItem{Key=b.Key,Text=b.Name});blend.SelectedKey=l.Blend;
            var opacity=Ui.Number(0,100,0,55);opacity.Value=l.Opacity;detail.AddRow(ToolUi.Row(new UiLabel{Text="混合"},blend,null));detail.AddRow(ToolUi.Row(new UiLabel{Text="不透明度 %"},opacity,null));
            type.SelectedValueChanged+=(_,_)=>{if(!EventsActive||type.IsDisposed)return;var key=type.SelectedKey??"";l.Kind=key.StartsWith("display:",StringComparison.Ordinal)?"display":key;l.Mode=l.Kind=="display"?Guid.Parse(key[8..]):Guid.Empty;owner.Changed(Row,false);RebuildLayers();};
            enabled.CheckedChanged+=(_,_)=>{if(!EventsActive||enabled.IsDisposed)return;l.Enabled=enabled.Checked==true;owner.Changed(Row,false);};blend.SelectedValueChanged+=(_,_)=>{if(!EventsActive||blend.IsDisposed)return;l.Blend=blend.SelectedKey??"norm";owner.Changed(Row,false);};opacity.ValueChanged+=(_,_)=>{if(!EventsActive||opacity.IsDisposed)return;l.Opacity=(int)opacity.Value;owner.Changed(Row,false);};
            if(l.Kind=="color")
            {
                var source=new DropDown{Width=100};source.Items.Add(new UiListItem{Key="material",Text="材质等效单色（贴图平均色）"});source.Items.Add(new UiListItem{Key="layer",Text="Rhino 图层颜色"});source.SelectedKey=l.ColorSource;
                detail.AddRow(new UiLabel{Text="颜色来源"});detail.AddRow(source);source.SelectedValueChanged+=(_,_)=>{if(!EventsActive||source.IsDisposed)return;l.ColorSource=source.SelectedKey??"material";owner.Changed(Row,false);};
            }
            if(l.Kind is "texture" or "color")
            {
                var grouping=new DropDown{Width=100};foreach(var (key,text) in new[]{("material","按材质合并（默认；图层色按颜色）"),("object","按物件分开 · 同一组"),("all","全部合并 · 一张图层")})grouping.Items.Add(new UiListItem{Key=key,Text=text});grouping.SelectedKey=l.TextureGrouping;
                detail.AddRow(new UiLabel{Text="分层方式"});detail.AddRow(grouping);grouping.SelectedValueChanged+=(_,_)=>{if(!EventsActive||grouping.IsDisposed)return;l.TextureGrouping=grouping.SelectedKey??"material";owner.Changed(Row,false);};
            }
            if(l.Kind=="plants")
            {
                var grouping=new DropDown{Width=100};foreach(var (key,text) in new[]{("individual","单株 · 学名子文件夹"),("species","按学名合并（默认）"),("all","全部植物合并为一层")})grouping.Items.Add(new UiListItem{Key=key,Text=text});grouping.SelectedKey=l.PlantGrouping;
                detail.AddRow(grouping);grouping.SelectedValueChanged+=(_,_)=>{if(!EventsActive||grouping.IsDisposed)return;l.PlantGrouping=grouping.SelectedKey??"species";owner.Changed(Row,false);};
            }
            if(l.Kind=="shadow")
            {
                var plantShadows=new UiCheckBox{Text="包含植物透空投影",Checked=Row.PlantShadows};
                var separate=new UiCheckBox{Text="分离植物阴影",Checked=Row.SeparatePlantShadows,Enabled=Row.PlantShadows};
                plantShadows.CheckedChanged+=(_,_)=>{if(!EventsActive||plantShadows.IsDisposed)return;Row.PlantShadows=plantShadows.Checked==true;separate.Enabled=Row.PlantShadows;owner.Changed(Row,false);};
                separate.CheckedChanged+=(_,_)=>{if(!EventsActive||separate.IsDisposed)return;Row.SeparatePlantShadows=separate.Checked==true;owner.Changed(Row,false);};
                detail.AddRow(plantShadows);detail.AddRow(new Panel{Padding=new(18,0,0,0),Content=separate});
                detail.AddRow(ToolUi.Note("分离后放在植物组最底层，沿用阴影通道的混合、透明度和眼睛；未启用植物通道时仍合并导出。"));
            }
            if(l.Kind=="depth")detail.AddRow(ToolUi.Note("相机方向的线性深度，近白远黑；按可见模型归一化，黑色背景不参与范围。植物按透明轮廓计入。"));
            var section=new UiExpander{Header=head,Content=detail,Expanded=l.Expanded};section.ExpandedChanged+=(_,_)=>{if(!EventsActive||section.IsDisposed)return;l.Expanded=section.Expanded;owner.PresentationChanged();};layerSections.Add(section);
            layout.AddRow(new UiGroupBox{Content=new Panel{Padding=new(4),Content=section}});
        }
        var old=layerHost.Content;layerHost.Content=layout;old?.Dispose();}finally{rebuilding=false;}
    }
    private void Move(int i,int d){(Row.Layers[i],Row.Layers[i+d])=(Row.Layers[i+d],Row.Layers[i]);RebuildLayers();owner.Changed(Row,false);}
    internal void RefreshPreview(){using var b=WorkbenchService.Preview(owner.Document,Row,506);Ui.Picture(image,frame,b,Math.Max(1,frame.Width),Math.Max(1,frame.Height));Loaded=true;}
    public void Dispose(){closed=true;image.Image?.Dispose();Root.Dispose();}
}

internal sealed class ViewDetails : IDisposable
{
    private readonly ExportPanel owner;
    internal ViewExportRow Row{get;}
    internal Scrollable Root{get;}
    private readonly ImageView image=new();
    private readonly PixelLayout frame=new(){Size=new(160,200),BackgroundColor=Color.FromArgb(30,34,39)};
    private readonly NumericStepper yaw=Ui.Number(-180,180,1),pitch=Ui.Number(-89,89,1),zoom=Ui.Number(.01,100,2),panX=Ui.Number(-1e9,1e9,3),panY=Ui.Number(-1e9,1e9,3),panZ=Ui.Number(-1e9,1e9,3),azimuth=Ui.Number(0,360,1),altitude=Ui.Number(.1,90,1);
    private readonly UiCheckBox documentSun=new(){Text="使用文档太阳"};
    private bool binding;private PointF? drag;
    internal ViewDetails(ExportPanel owner,ViewExportRow row)
    {
        this.owner=owner;Row=row;frame.Add(image,0,0);frame.SizeChanged+=(_,_)=>Ui.FitPicture(image,frame);
        image.MouseDown+=(_,e)=>{if(e.Buttons.HasFlag(MouseButtons.Primary))drag=e.Location;};image.MouseUp+=(_,_)=>drag=null;
        image.MouseMove+=(_,e)=>{if(drag is not {} p||!e.Buttons.HasFlag(MouseButtons.Primary))return;row.Camera.Yaw=Math.Clamp(row.Camera.Yaw+(e.Location.X-p.X)*.35,-180,180);row.Camera.Pitch=Math.Clamp(row.Camera.Pitch+(e.Location.Y-p.Y)*.35,-89,89);drag=e.Location;Sync();owner.Changed(row);};
        image.MouseWheel+=(_,e)=>{row.Camera.Zoom=Math.Clamp(row.Camera.Zoom*Math.Pow(1.1,Math.Sign(e.Delta.Height)),.01,100);Sync();owner.Changed(row);};
        foreach(var n in new[]{yaw,pitch,zoom,panX,panY,panZ,azimuth,altitude})n.ValueChanged+=(_,_)=>Apply();documentSun.CheckedChanged+=(_,_)=>Apply();
        var mode=Ui.Modes(row.Mode);mode.SelectedValueChanged+=(_,_)=>{if(Guid.TryParse(mode.SelectedKey,out var id)){row.Mode=id;owner.Changed(row);}};
        var top=Ui.Layout();top.AddRow(Ui.Button("← 返回全部视图",owner.CloseDetails));top.AddRow(new UiLabel{Text=row.Name,Tag="user-content",Font=new Font(SystemFont.Bold,13)});top.AddRow(mode);top.AddRow(Ui.Button("刷新预览",()=>owner.Guard(RefreshPreview)));
        var camera=Ui.Layout();foreach(var item in new[]{("水平旋转 °",yaw),("俯仰 °",pitch),("缩放",zoom),("目标平移 X",panX),("目标平移 Y",panY),("目标平移 Z",panZ)})camera.AddRow(new UiLabel{Text=item.Item1},item.Item2,null);
        camera.AddRow(Ui.Button("重置相机",()=>{row.Camera=new();Sync();owner.Changed(row);}));camera.AddRow(Ui.Button("写回 Named View 相机",()=>owner.Guard(()=>{WorkbenchService.WriteBack(owner.Document,row);owner.CloseDetails();owner.RefreshNamedViews();owner.Changed(row);})));
        var sun=Ui.Layout();sun.AddRow(documentSun);sun.AddRow(new UiLabel{Text="太阳方位 °"},azimuth,null);sun.AddRow(new UiLabel{Text="高度 °"},altitude,null);
        var content=Ui.Layout();content.Padding=new(6);content.AddRow(top);content.AddRow(frame);
        content.AddRow(new UiLabel{Text="拖动旋转，滚轮缩放。相机 / 太阳只用于此视图导出；写回按钮只更新 Named View 相机。",Wrap=WrapMode.Word});content.AddRow(camera);content.AddRow(sun);
        content.AddRow(new UiLabel{Text="太阳设置同时用于显示模式和独立阴影通道；独立阴影不包含反射 / GI / AO。",Wrap=WrapMode.Word});content.AddRow(null);Root=ToolUi.VerticalScroll(content);Sync();
    }
    private void Sync(){binding=true;try{var c=Row.Camera;yaw.Value=c.Yaw;pitch.Value=c.Pitch;zoom.Value=c.Zoom;panX.Value=c.PanX;panY.Value=c.PanY;panZ.Value=c.PanZ;documentSun.Checked=Row.Sun.UseDocument;azimuth.Value=Row.Sun.Azimuth;altitude.Value=Row.Sun.Altitude;azimuth.Enabled=altitude.Enabled=!Row.Sun.UseDocument;}finally{binding=false;}}
    private void Apply(){if(binding)return;var c=Row.Camera;c.Yaw=yaw.Value;c.Pitch=pitch.Value;c.Zoom=zoom.Value;c.PanX=panX.Value;c.PanY=panY.Value;c.PanZ=panZ.Value;Row.Sun.UseDocument=documentSun.Checked==true;Row.Sun.Azimuth=azimuth.Value;Row.Sun.Altitude=altitude.Value;azimuth.Enabled=altitude.Enabled=!Row.Sun.UseDocument;owner.Changed(Row);}
    internal void RefreshPreview(){using var b=WorkbenchService.Preview(owner.Document,Row,600);Ui.Picture(image,frame,b,Math.Max(1,frame.Width),Math.Max(1,frame.Height));}
    public void Dispose(){image.Image?.Dispose();Root.Dispose();}
}
