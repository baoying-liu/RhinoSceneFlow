using Eto.Drawing;
using Eto.Forms;
using Rhino;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class MaterialsTool:Panel
{
    private readonly uint document;
    private readonly MaterialChatView? chat;
    private readonly bool libraryOnly;
    private readonly MaterialActionQueue actions;
    private readonly UITimer poll=new(){Interval=.25};
    private readonly Label target=new(),status=new(){Text="描述材质，或从材质库中选择。",Wrap=WrapMode.Word},chosen=new(){Text="尚未选择材质",Wrap=WrapMode.Word};
    private readonly ProgressBar progress=new(){MaxValue=100};
    private readonly DropDown scope=new();
    private readonly CheckBox reuse=new(){Text="优先复用相似的已有材质",Checked=true};
    private readonly NumericStepper width=Ui.Number(.001,1e8,1,95),height=Ui.Number(.001,1e8,1,95);
    private readonly NumericStepper roughness=Ui.Number(0,1,2,95),metallic=Ui.Number(0,1,2,95);
    private readonly DropDown randomMode=new(),randomTiles=new();
    private readonly NumericStepper randomSeed=Ui.Number(int.MinValue,int.MaxValue,0,110),randomStrength=Ui.Number(0,50,0,85),randomColumns=Ui.Number(1,128,0,65),randomRows=Ui.Number(1,128,0,65),randomOffset=Ui.Number(0,1,2,65);
    private readonly CheckBox randomRotate=new(){Text="允许旋转（非方形仅 180°）"};
    private readonly Label randomReason=new(){Wrap=WrapMode.Word,Width=260},randomSummary=new(){Wrap=WrapMode.Word};
    private readonly Panel randomGrid=new();
    private readonly Expander randomSettings;
    private readonly Panel candidateHost=new();
    private readonly MaterialShelf? shelf;
    private readonly Button apply;
    private readonly Button cancel;
    private readonly Control[] appearanceControls;
    private bool plantContext;
    private readonly SeasonalAssetPanel seasonal=new(false);
    private Guid? selected,job,lastJob,randomPreview;
    private MaterialAsset? selectedVersion;
    private bool closed,documentClosed;
    internal bool LocalBusy=>actions.Busy||job.HasValue||randomPreview.HasValue;
    public bool Busy=>!documentClosed&&(LocalBusy||SceneFlowWorkspace.OtherMaterialBusy(document,this));
    public uint DocumentSerial=>document;
    private RhinoDoc Doc=>RhinoDoc.FromRuntimeSerialNumber(document)??throw new InvalidOperationException("文档已关闭。");
    public MaterialsTool(RhinoDoc doc,bool libraryOnly=false)
    {
        document=doc.RuntimeSerialNumber;this.libraryOnly=libraryOnly;actions=new(document,(s,p)=>SceneFlowWorkspace.MaterialProgress(document,s,p));
        width.Value=height.Value=1000;scope.Items.Add(new ListItem{Key="object",Text="应用到当前物件"});scope.Items.Add(new ListItem{Key="layer",Text="应用到物件所在图层"});scope.SelectedIndex=0;
        scope.SelectedKey=SceneFlowWorkspace.MaterialScope(document);
        scope.SelectedValueChanged+=(_,_)=>{if(scope.SelectedKey is "object" or "layer")SceneFlowWorkspace.SetMaterialScope(document,scope.SelectedKey);};
        if(libraryOnly)shelf=new(doc,SelectAsset);
        else chat=new(document,()=>(width.Value/1000,height.Value/1000),id=>{job=lastJob=id;progress.Indeterminate=true;},()=>reuse.Checked==true);
        var settings=Ui.Layout();settings.AddRow(new Label{Text="整张贴图代表的实际宽 × 高（mm）",Wrap=WrapMode.Word});settings.AddRow(ToolUi.Row(width,new Label{Text="×"},height,null));
        settings.AddRow(ToolUi.Row(new Label{Text="粗糙度"},roughness,null));settings.AddRow(ToolUi.Row(new Label{Text="金属度"},metallic,null));
        settings.AddRow(Ui.Button("保存尺寸与外观参数",()=>Guard(()=>{if(Busy)throw new ArgumentException("请先完成当前任务。");if(selectedVersion==null)throw new ArgumentException("先选择材质。");var a=MaterialLibrary.Clone(selectedVersion);a.WidthMeters=width.Value/1000;a.HeightMeters=height.Value/1000;a.Roughness=roughness.Value;a.Metallic=metallic.Value;MaterialService.Library.Update(a);SelectAsset(a.Id);status.Text="尺寸与外观参数已保存，下次应用生效。";})));
        settings.AddRow(Ui.Button("打开 UV 工具",()=>SceneFlowWorkspace.Open("uv")));
        var advanced=new Expander{Header="尺寸与高级设置",Expanded=false,Content=settings};
        foreach(var item in new[]{("auto","自动 · 使用 AI 建议"),("off","关闭"),("object","按物件随机"),("stochastic","自然纹理 · 随机平铺"),("macro","大尺度色差"),("structured","保留结构 · 分区色差")})randomMode.Items.Add(new ListItem{Key=item.Item1,Text=item.Item2});
        foreach(int n in new[]{2,4,8})randomTiles.Items.Add(new ListItem{Key=n.ToString(),Text=$"{n} × {n} 个原图周期"});
        var grid=Ui.Layout();grid.AddRow(new Label{Text="原图包含的列 × 行（不确定时保持 1 × 1）",Wrap=WrapMode.Word});grid.AddRow(ToolUi.Row(randomColumns,new Label{Text="×"},randomRows,null));grid.AddRow(ToolUi.Row(new Label{Text="错缝比例"},randomOffset,null));randomGrid.Content=grid;
        var random=Ui.Layout();random.AddRow(randomMode);random.AddRow(randomReason);random.AddRow(ToolUi.Row(new Label{Text="随机种子"},randomSeed,null));random.AddRow(ToolUi.Row(new Label{Text="色差 %"},randomStrength,null));random.AddRow(randomTiles);random.AddRow(randomRotate);random.AddRow(randomGrid);
        random.AddRow(new Label{Text="保留真实尺寸与原图清晰度；大周期需要更多缓存。按物件模式会为图层内现有物件建立独立外观变体。",Wrap=WrapMode.Word,Width=260});
        random.AddRow(Ui.Button("保存并预览",()=>Guard(()=>{if(Busy)throw new InvalidOperationException("请先完成当前任务。");SaveRandom();randomPreview=RandomTextureService.Start(Doc,selected!.Value,preview:true).Id;})));
        randomSettings=new Expander{Header="随机去重复",Expanded=false,Content=new Scrollable{Content=random,ExpandContentWidth=true,Height=260}};randomMode.SelectedValueChanged+=(_,_)=>UpdateRandomSummary();randomMode.SelectedKey="off";randomTiles.SelectedKey="4";randomSeed.Value=42;randomStrength.Value=15;randomColumns.Value=randomRows.Value=1;randomOffset.Value=.5;
        var settingsBody=Ui.Layout();settingsBody.AddRow(randomSummary);settingsBody.AddRow(randomSettings);settingsBody.AddRow(advanced);
        var materialSettings=new Expander{Header="铺贴与外观设置",Expanded=false,Content=new Scrollable{Content=settingsBody,ExpandContentWidth=true,Height=240}};
        appearanceControls=[randomSummary,materialSettings,scope];
        var l=Ui.Layout();l.AddRow(ToolUi.Heading(libraryOnly?"材质库":"AI 素材对话"));l.AddRow(target);
        if(libraryOnly)l.Add(new Scrollable{Content=shelf!,ExpandContentWidth=true,ExpandContentHeight=false},true,true);
        else{reuse.Text="优先查找已有素材";l.AddRow(reuse);var fourSeasons=new CheckBox{Text="生成四季版本（默认只生成夏季）",Checked=PluginPreferences.Load().GenerateFourSeasons};fourSeasons.CheckedChanged+=(_,_)=>{var preferences=PluginPreferences.Load();preferences.GenerateFourSeasons=fourSeasons.Checked==true;PluginPreferences.Save(preferences);};l.AddRow(fourSeasons);l.AddRow(ToolUi.Pair(Ui.Button("浏览材质库",()=>ShowLibrary(true)),Ui.Button("浏览植物库",()=>SceneFlowWorkspace.Open("planting"))));l.Add(chat!,true,true);l.AddRow(candidateHost);}
        var application=Ui.Layout();application.AddRow(chosen);application.AddRow(scope);apply=Ui.Button("应用选中材质",Apply);application.AddRow(apply);
        l.AddRow(ToolUi.Section("应用材质",application));l.AddRow(materialSettings);l.AddRow(seasonal);
        progress.Visible=false;cancel=Ui.Button("取消当前任务",Cancel);cancel.Visible=false;
        l.AddRow(progress);l.AddRow(status);l.AddRow(cancel);
        Content=l;
        if(SceneFlowWorkspace.SelectedAsset(document) is Guid asset)Guard(()=>ReceiveAsset(asset));
        Load+=(_,_)=>Activate();poll.Elapsed+=(_,_)=>Tick();poll.Start();
        RhinoDoc.CloseDocument+=OnDocumentClosed;
    }
    private void OnDocumentClosed(object? sender,DocumentEventArgs e)
    {
        if(e.Document.RuntimeSerialNumber!=document||documentClosed)return;
        documentClosed=true;poll.Stop();actions.Dispose();if(job.HasValue)MaterialChat.Cancel(job.Value);if(randomPreview.HasValue)RandomTextureService.Cancel(randomPreview.Value);chat?.Stop();shelf?.Stop();
    }
    internal void Activate(){if(!closed&&!documentClosed&&chat!=null)_=chat.StartAsync();}
    public void ShowLibrary(bool visible)=>SceneFlowWorkspace.Open(visible?"library":"materials");
    public void SelectAsset(Guid id)=>SceneFlowWorkspace.SelectAsset(document,id);
    internal void ReceiveScope(string value){if(scope.SelectedKey!=value)scope.SelectedKey=value;}
    internal void ReceiveProgress(string message,int percent){if(closed)return;status.Text=message;progress.Indeterminate=false;progress.Value=percent;}
    internal void ReceiveAsset(Guid id)
    {
        seasonal.Bind(id);
        plantContext=false;foreach(var control in appearanceControls)control.Visible=true;apply.Text="应用选中材质";
        var a=MaterialService.Library.Get(id);selected=id;selectedVersion=MaterialLibrary.Clone(a);width.Value=a.WidthMeters*1000;height.Value=a.HeightMeters*1000;roughness.Value=a.Roughness;metallic.Value=a.Metallic;chosen.Text=a.Name+" · "+a.Category;status.Text="材质已选中；点击应用即可。";
        var r=a.Randomization;randomMode.SelectedKey=r.Mode;randomTiles.SelectedKey=r.Tiles.ToString();randomSeed.Value=r.Seed;randomStrength.Value=r.Strength*100;randomRotate.Checked=r.Rotate;randomColumns.Value=r.Columns;randomRows.Value=r.Rows;randomOffset.Value=r.RowOffset;randomReason.Text=(r.RecommendedBy=="ai"?"AI 建议：":"")+r.Reason;UpdateRandomSummary();
        if(shelf!=null){shelf.Refresh();shelf.Select(id,false);}
    }
    public void Configure(bool? reuseSimilar=null,string? applyScope=null)
    {
        if(Busy)throw new InvalidOperationException("当前任务尚未完成。");
        if(applyScope!=null&&applyScope is not ("object" or "layer"))throw new ArgumentException("scope: object | layer");
        if(reuseSimilar.HasValue)reuse.Checked=reuseSimilar.Value;if(applyScope!=null)scope.SelectedKey=applyScope;
    }
    public void Apply()=>Guard(()=>
    {
        if(plantContext){SceneFlowWorkspace.Open("planting");return;}
        if(Busy)throw new ArgumentException("请先完成当前任务。");if(selected==null)throw new ArgumentException("先生成或选择材质。");var t=ToolUi.Targets(Doc,scope.SelectedKey=="layer");
        if(selectedVersion!=null&&MaterialService.Serialize(RandomDraft())!=MaterialService.Serialize(selectedVersion.Randomization))SaveRandom();
        actions.Start(t.Objects,t.Layers,new(),selected);status.Text="正在检查随机贴图与真实尺寸 UV…";
    });
    private TextureRandomization RandomDraft(){var r=MaterialLibrary.Clone(selectedVersion?.Randomization??new());r.Mode=randomMode.SelectedKey??"off";r.Seed=(int)randomSeed.Value;r.Strength=randomStrength.Value/100;r.Tiles=int.Parse(randomTiles.SelectedKey??"4");r.Rotate=randomRotate.Checked==true;r.Columns=(int)randomColumns.Value;r.Rows=(int)randomRows.Value;r.RowOffset=randomOffset.Value;return r;}
    private void SaveRandom(){if(selectedVersion==null)throw new ArgumentException("先生成或选择材质。");var a=MaterialLibrary.Clone(selectedVersion);a.Randomization=RandomDraft();if(MaterialService.Serialize(a.Randomization)!=MaterialService.Serialize(selectedVersion.Randomization))MaterialService.Library.Update(a);SelectAsset(a.Id);}
    private void UpdateRandomSummary(){string mode=randomMode.SelectedKey??"off";if(mode=="auto")mode=selectedVersion?.Randomization.RecommendedMode??"off";randomGrid.Visible=mode=="structured";randomSummary.Text="去重复 · "+(mode switch{"object"=>"按物件随机","stochastic"=>"自然纹理随机平铺","macro"=>"大尺度色差","structured"=>"保留结构分区色差",_=>"关闭"});}
    public void Cancel(){actions.Cancel();if(job.HasValue)MaterialChat.Cancel(job.Value);if(randomPreview.HasValue)RandomTextureService.Cancel(randomPreview.Value);}
    private void Guard(Action a){if(closed||documentClosed)return;try{a();}catch(Exception e){status.Text=e.Message;}}
    private void Tick()
    {
        if(closed||documentClosed)return;
        Guard(()=>
        {
            int count=ToolUi.Selection(Doc).Length;target.Text=count>0?$"当前选择 · {count} 个物件":"在 Rhino 中选择物件后可应用材质";apply.Enabled=!Busy&&(plantContext||selected.HasValue&&count>0);reuse.Enabled=!job.HasValue;randomSettings.Enabled=!Busy;progress.Visible=cancel.Visible=Busy;
            if(randomPreview.HasValue){var p=RandomTextureService.Get(randomPreview.Value);status.Text=p.Stage;progress.Value=p.Percent;if(p.Status=="running")return;randomPreview=null;if(p.Status=="completed"&&selected.HasValue){SceneFlowWorkspace.Open("library");SelectAsset(selected.Value);}return;}
            if(!job.HasValue)return;var j=MaterialChat.Get(job.Value);status.Text=j.Stage;
            if(j.Status=="running")return;job=null;progress.Indeterminate=false;
            plantContext=j.Kind=="plant";foreach(var control in appearanceControls)control.Visible=!plantContext;apply.Text=plantContext?"打开植物库与种植":"应用选中材质";
            if(plantContext)chosen.Text="植物素材 · 在植物库中选择并种植";
            if(j.Material.HasValue)SelectAsset(j.Material.Value);
            if(j.Plant.HasValue){PlantService.Selected[document]=j.Plant.Value;SceneFlowWorkspace.Planting?.Refresh();SceneFlowWorkspace.Planting?.Select(j.Plant.Value);}
            var list=Ui.Layout();foreach(var match in j.Matches){var a=MaterialService.Library.Get(match.Id);list.AddRow(Ui.Button(a.Name+" · "+match.Reason,()=>Guard(()=>SelectAsset(a.Id))));}
            foreach(var match in j.PlantMatches){var a=PlantService.Library.Get(match.Id);list.AddRow(Ui.Button(a.Name+" · "+a.Plant!.ScientificName+" · "+match.Reason,()=>Guard(()=>{PlantService.Selected[document]=a.Id;SceneFlowWorkspace.Open("planting");SceneFlowWorkspace.Planting?.Select(a.Id);})));}
            candidateHost.Content=j.Matches.Length+j.PlantMatches.Length>0?new Expander{Header="找到可复用素材 · 选择后应用／种植",Expanded=true,Content=list}:null;
        });
    }
    public object GetState()=>new{open=!closed,page=libraryOnly?"library":"materials",document,selected,job,lastJob,randomPreview,randomization=selectedVersion?.Randomization,chatKit=chat?.State,chatTheme=chat?.Theme,busy=Busy,scope=scope.SelectedKey,reuseSimilar=reuse.Checked,shelf=shelf?.GetState(),status=status.Text};
    protected override void Dispose(bool disposing)
    {
        if(disposing)
        {
            if(closed)return;closed=true;RhinoDoc.CloseDocument-=OnDocumentClosed;
            poll.Stop();poll.Dispose();actions.Dispose();if(job.HasValue)MaterialChat.Cancel(job.Value);if(randomPreview.HasValue)RandomTextureService.Cancel(randomPreview.Value);
            // DynamicLayout keeps logical rows separately from the native tree.
            // Clear those references, detach children while parents are alive,
            // then release children and finally their enclosing layout.
            var root=Content;Content=null;if(root is DynamicLayout layout)layout.Clear();
            chat?.Dispose();shelf?.Dispose();root?.Dispose();
        }
        base.Dispose(disposing);
    }
}

public sealed class MaterialShelf:Panel
{
    private readonly uint document;
    private readonly Action<Guid> select;
    private readonly TextBox search=new(){PlaceholderText="搜索名称、分类或标签"},name=new(),categoryEdit=new(),tagsEdit=new();
    private readonly DropDown category=new(),tag=new();
    private readonly GridView list=new(){ShowHeader=false,AllowMultipleSelection=false,Height=230};
    private readonly ImageView preview=new(){Size=new(260,180)};
    private readonly Label details=new(){Wrap=WrapMode.Word},status=new(){Wrap=WrapMode.Word};
    private readonly Panel inspector=new();
    private readonly UITimer poll=new(){Interval=.5};
    private readonly Dictionary<Guid,Bitmap> swatches=[];
    private Guid? selected,organize;
    private int? selectedRevision;
    private bool binding,closed,stopped;
    private MaterialAsset[] catalog=[];
    private string catalogStamp="";
    private DateTime nextRefresh;
    private object[][] rows=[];
    public Guid? SelectedAsset=>selected;
    public MaterialShelf(RhinoDoc doc,Action<Guid> select)
    {
        document=doc.RuntimeSerialNumber;this.select=select;
        list.Columns.Add(new GridColumn{DataCell=new ImageViewCell(0),Width=36});list.Columns.Add(new GridColumn{DataCell=new TextBoxCell(1),Width=220});
        var refresh=Ui.Button("↻",Refresh,32);refresh.ToolTip="刷新材质库";
        var l=Ui.Layout();l.AddRow(new TableLayout{Spacing=new(6,0),Rows={new TableRow(new TableCell(search,true),refresh)}});l.AddRow(new Label{Text="分类"});l.AddRow(category);l.AddRow(new Label{Text="标签"});l.AddRow(tag);l.AddRow(list);l.AddRow(details);l.AddRow(status);l.AddRow(inspector);
        BuildInspector();inspector.Visible=false;
        var advanced=Ui.Layout();advanced.AddRow(Ui.Button("导入图片…",Import));advanced.AddRow(Ui.Button("AI 整理名称、分类与标签",()=>Guard(()=>{organize=CatalogService.Organize().Id;status.Text="正在整体优化分类、标签与名称…";})));advanced.AddRow(Ui.Button("切换材质库文件夹…",()=>Guard(()=>{using var dialog=new SelectFolderDialog{Directory=MaterialService.Library.Root};if(dialog.ShowDialog(this)==DialogResult.Ok){SceneFlowPlugin.Instance.MaterialDirectory=dialog.Directory;Refresh();}})));advanced.AddRow(ToolUi.Note("尺寸、外观与随机去重复可在下方“铺贴与外观设置”调整。"));l.AddRow(new Expander{Header="库管理",Content=advanced});Content=l;
        search.TextChanged+=(_,_)=>Filter();category.SelectedValueChanged+=(_,_)=>{if(!binding){FillTags();Filter();}};tag.SelectedValueChanged+=(_,_)=>{if(!binding)Filter();};
        list.SelectionChanged+=(_,_)=>{if(!binding&&list.SelectedRow>=0&&list.SelectedRow<rows.Length)Guard(()=>Select((Guid)rows[list.SelectedRow][2]));};
        poll.Elapsed+=(_,_)=>Guard(()=>{if(stopped)return;if(DateTime.UtcNow>=nextRefresh){nextRefresh=DateTime.UtcNow.AddSeconds(2);var assets=MaterialService.Library.List();if(Stamp(assets)!=catalogStamp)Refresh();}if(organize==null)return;var j=CatalogService.Get(organize.Value);status.Text=j.Stage;if(j.Status!="running"){organize=null;if(j.Status=="completed")Refresh();}});poll.Start();Refresh();
    }
    private static string Stamp(MaterialAsset[] assets)=>MaterialService.Library.Root+string.Join(";",assets.OrderBy(a=>a.Id).Select(a=>$"{a.Id}/{a.Revision}/{a.CatalogRevision}"));
    private void Guard(Action a){if(closed)return;try{a();}catch(Exception e){status.Text=e.Message;}}
    public void Refresh()
    {
        if(closed)return;catalog=MaterialService.Library.List();catalogStamp=Stamp(catalog);nextRefresh=DateTime.UtcNow.AddSeconds(2);binding=true;try{string old=category.SelectedKey??"";category.Items.Clear();category.Items.Add(new ListItem{Key="",Text="所有分类"});foreach(var c in catalog.Select(a=>a.Category).Where(c=>c.Length>0).Distinct().Order())category.Items.Add(new ListItem{Key=c,Text=c});category.SelectedKey=old;if(category.SelectedIndex<0)category.SelectedIndex=0;}finally{binding=false;}FillTags();Filter();
    }
    private void FillTags()
    {
        binding=true;try{string old=tag.SelectedKey??"";tag.Items.Clear();tag.Items.Add(new ListItem{Key="",Text="所有标签"});foreach(var t in MaterialCatalog.Filter(catalog,category:category.SelectedKey??"").SelectMany(a=>a.Tags).Distinct().Order())tag.Items.Add(new ListItem{Key=t,Text=t});tag.SelectedKey=old;if(tag.SelectedIndex<0)tag.SelectedIndex=0;}finally{binding=false;}
    }
    private void Filter()=>Guard(()=>
    {
        binding=true;try{rows=MaterialCatalog.Filter(catalog,search.Text,category.SelectedKey??"",tag.SelectedKey??"").Select(a=>new object[]{Swatch(a),a.Name+"\n"+a.Category,a.Id}).ToArray();list.DataStore=rows;list.SelectedRow=selected.HasValue?Array.FindIndex(rows,r=>(Guid)r[2]==selected.Value):-1;details.Text=$"{rows.Length} 个材质";}finally{binding=false;}
    });
    private Bitmap Swatch(MaterialAsset asset)
    {
        if(swatches.TryGetValue(asset.Id,out var value))return value;
        using var original=new System.Drawing.Bitmap(MaterialService.Library.MapPath(asset,"baseColor"));using var small=new System.Drawing.Bitmap(original,16,16);long r=0,g=0,b=0;for(int y=0;y<16;y++)for(int x=0;x<16;x++){var c=small.GetPixel(x,y);r+=c.R;g+=c.G;b+=c.B;}
        using var circle=new System.Drawing.Bitmap(28,28);using(var gfx=System.Drawing.Graphics.FromImage(circle)){gfx.SmoothingMode=System.Drawing.Drawing2D.SmoothingMode.AntiAlias;gfx.Clear(System.Drawing.Color.Transparent);using var brush=new System.Drawing.SolidBrush(System.Drawing.Color.FromArgb((int)(r/256),(int)(g/256),(int)(b/256)));gfx.FillEllipse(brush,2,2,24,24);}value=Ui.Bitmap(circle);swatches.Add(asset.Id,value);return value;
    }
    public void Select(Guid id,bool notify=true)
    {
        if(notify){select(id);return;}
        var a=MaterialService.Library.Get(id);selected=id;selectedRevision=a.CatalogRevision;name.Text=a.Name;categoryEdit.Text=a.Category;tagsEdit.Text=string.Join("，",a.Tags);
        binding=true;try{list.SelectedRow=Array.FindIndex(rows,r=>(Guid)r[2]==id);}finally{binding=false;}
        using(var original=new System.Drawing.Bitmap(MaterialService.Library.MapPath(a,"baseColor")))
        using(var thumb=new System.Drawing.Bitmap(original,260,180)){var old=preview.Image;preview.Image=Ui.Bitmap(thumb);old?.Dispose();}
        inspector.Visible=true;status.Text=$"{a.WidthMeters:G4} × {a.HeightMeters:G4} m · {string.Join(" · ",a.Tags)}";
        try{using var sphere=NativeMaterialPreview.Render(a);var old=preview.Image;preview.Image=Ui.Bitmap(sphere);old?.Dispose();}catch(Exception e){status.Text+="\n"+e.Message;}
        if(a.Randomization.ResolvedMode!="off"&&RandomTextureService.TryResolve(MaterialService.Library,a,Guid.Empty)==null)status.Text+="\n随机缓存尚未准备，球体暂显示原图。";
    }
    private void BuildInspector()
    {
        var edit=Ui.Layout();edit.AddRow(preview);edit.AddRow(Ui.Button("查看球体上的效果",()=>Guard(()=>{if(selected==null)return;using var b=NativeMaterialPreview.Render(MaterialService.Library.Get(selected.Value));var old=preview.Image;preview.Image=Ui.Bitmap(b);old?.Dispose();status.Text="Rhino 原生着色球体预览 · 示意铺贴效果。";})));
        var fields=Ui.Layout();fields.AddRow(new Label{Text="名称"});fields.AddRow(name);fields.AddRow(new Label{Text="分类"});fields.AddRow(categoryEdit);fields.AddRow(new Label{Text="标签（逗号分隔）"});fields.AddRow(tagsEdit);
        fields.AddRow(Ui.Button("保存属性",()=>Guard(()=>{if(selected==null)return;MaterialService.Library.UpdateLabels(selected.Value,name.Text,categoryEdit.Text,tagsEdit.Text.Split([',','，',';','；'],StringSplitOptions.RemoveEmptyEntries),selectedRevision);Refresh();Select(selected.Value);status.Text="分类、名称与标签已更新。";})));
        edit.AddRow(new Expander{Header="编辑名称、分类与标签",Content=fields});inspector.Content=edit;
    }
    private void Import()=>Guard(()=>
    {
        using var dialog=new OpenFileDialog();dialog.Filters.Add(new FileFilter("材质图片",".png",".jpg",".jpeg"));if(dialog.ShowDialog(this)!=DialogResult.Ok)return;
        var a=MaterialService.Import(new(){Name=Path.GetFileNameWithoutExtension(dialog.FileName),Category="待分类",Tags=["导入"]},new(){{"baseColor",dialog.FileName}});Select(a.Id);Refresh();status.Text="图片已导入；请在高级设置中确认实际尺寸。";
    });
    public object GetState()=>new{selected,organize,category=category.SelectedKey,tag=tag.SelectedKey,query=search.Text,count=rows.Length,status=status.Text};
    internal void Stop(){stopped=true;poll.Stop();if(organize.HasValue)CatalogService.Cancel(organize.Value);}
    protected override void Dispose(bool disposing){if(disposing){if(closed)return;closed=true;Stop();poll.Dispose();var image=preview.Image;preview.Image=null;image?.Dispose();list.DataStore=null;foreach(var b in swatches.Values)b.Dispose();}base.Dispose(disposing);}
}
