using System.Collections.ObjectModel;
using Eto.Drawing;
using Eto.Forms;
using Rhino;
using Rhino.Display;
using Rhino.UI;
using Rhino.UI.Controls;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class ViewExportRow
{
    public Guid Id { get; init; }
    public string Name { get; set; }="";
    public bool Included { get; set; }=true;
    public int Width { get; set; }
    public int Height { get; set; }
    public Guid Mode { get; set; }=DisplayModeDescription.ShadedId;
    public string Status { get; set; }="待导出";
}

public static class ExportPanelController
{
    private static readonly Dictionary<uint,ExportPanel> windows=[];
    public static ExportPanel Open(RhinoDoc doc)
    {
        NamedViewExportService.RequireActive(doc);
        if(windows.TryGetValue(doc.RuntimeSerialNumber,out var old)){old.BringToFront();return old;}
        var panel=new ExportPanel(doc);windows[doc.RuntimeSerialNumber]=panel;
        panel.Closed+=(_,_)=>windows.Remove(doc.RuntimeSerialNumber);
        panel.Owner=RhinoEtoApp.MainWindowForDocument(doc);panel.Show();return panel;
    }
    public static ExportPanel? Find(uint document)=>windows.GetValueOrDefault(document);
}

/// <summary>Modeless native Eto UI, with Rhino's own embedded viewport control.</summary>
public sealed class ExportPanel : Form
{
    private readonly uint document;
    private readonly ObservableCollection<ViewExportRow> rows=[];
    private readonly GridView grid=new(){AllowMultipleSelection=false};
    private readonly NumericStepper width=new(){MinValue=64,MaxValue=8192,DecimalPlaces=0,Width=100};
    private readonly NumericStepper height=new(){MinValue=64,MaxValue=8192,DecimalPlaces=0,Width=100};
    private readonly DropDown modes=new(){Width=180};
    private readonly ViewportControl preview=new();
    private readonly PixelLayout previewHost=new(){BackgroundColor=Color.FromArgb(36,39,43)};
    private readonly Label frameLabel=new(){Text="选择 Named View 查看预览"};
    private readonly Label status=new(){Text="就绪"};
    private readonly CheckBox material=new(){Text="材质 / 图层色",Checked=true};
    private readonly CheckBox shadow=new(){Text="阴影",Checked=true};
    private readonly TextBox folder=new();
    private readonly Button export=new(){Text="批量导出 PSD"};
    private readonly Button cancel=new(){Text="取消导出",Enabled=false};
    private readonly ProgressBar progress=new(){MinValue=0,MaxValue=1};
    private readonly TextArea log=new(){ReadOnly=true,Height=85,Wrap=false};
    private readonly DynamicLayout options=new(){Spacing=new(8,8)};
    private readonly DynamicLayout viewTools=new(){Spacing=new(6,6)};
    private readonly DynamicLayout outputOptions=new(){Spacing=new(8,8)};
    private bool binding,busy,shown,documentClosed;
    private CancellationTokenSource? cancellation;
    public BatchReport? LastReport { get; private set; }
    private ViewExportRow? Selected=>grid.SelectedItem as ViewExportRow;
    private RhinoDoc Doc=>RhinoDoc.FromRuntimeSerialNumber(document)??throw new InvalidOperationException("文档已关闭。");

    public ExportPanel(RhinoDoc doc)
    {
        document=doc.RuntimeSerialNumber;
        Title="RhinoSceneFlow · Named View 批量导出";
        ClientSize=new(1120,780);MinimumSize=new(940,660);Padding=new(14);
        folder.Text=SceneFlowPlugin.Instance.ExportDirectory;
        var refresh=new Button{Text="刷新 Named Views"};refresh.Click+=(_,_)=>Guard(RefreshNamedViews);
        var all=new Button{Text="全选"};all.Click+=(_,_)=>{foreach(var row in rows)row.Included=true;grid.ReloadData(Enumerable.Range(0,rows.Count));};
        var none=new Button{Text="全不选"};none.Click+=(_,_)=>{foreach(var row in rows)row.Included=false;grid.ReloadData(Enumerable.Range(0,rows.Count));};
        viewTools.AddRow(new StackLayout{Orientation=Orientation.Horizontal,Spacing=6,Items={refresh,all,none}});
        grid.Columns.Add(new GridColumn{HeaderText="导出",DataCell=new CheckBoxCell(nameof(ViewExportRow.Included)),Editable=true,Width=48});
        grid.Columns.Add(new GridColumn{HeaderText="Named View",DataCell=new TextBoxCell(nameof(ViewExportRow.Name)),AutoSize=true,Expand=true});
        grid.Columns.Add(new GridColumn{HeaderText="宽",DataCell=new TextBoxCell(nameof(ViewExportRow.Width)),Width=55});
        grid.Columns.Add(new GridColumn{HeaderText="高",DataCell=new TextBoxCell(nameof(ViewExportRow.Height)),Width=55});
        grid.Columns.Add(new GridColumn{HeaderText="状态",DataCell=new TextBoxCell(nameof(ViewExportRow.Status)),Width=90});
        grid.DataStore=rows;
        grid.SelectionChanged+=(_,_)=>BindSelection();
        var left=new DynamicLayout{Spacing=new(8,8)};left.AddRow(viewTools);left.Add(grid,true,true);
        left.AddRow(new Label{Text="勾选要导出的视图；选中行可编辑尺寸。"});
        width.ValueChanged+=(_,_)=>UpdateSize();height.ValueChanged+=(_,_)=>UpdateSize();
        foreach(var mode in DisplayModeDescription.GetDisplayModes())
            modes.Items.Add(new ListItem{Key=mode.Id.ToString(),Text=mode.LocalName});
        modes.SelectedValueChanged+=(_,_)=>
        {
            if(!binding&&Selected is { } row && Guid.TryParse(modes.SelectedKey,out var mode))
            {row.Mode=mode;Guard(RefreshPreview);}
        };
        var refreshPreview=new Button{Text="刷新预览"};refreshPreview.Click+=(_,_)=>Guard(RefreshPreview);
        var browse=new Button{Text="选择文件夹…"};browse.Click+=(_,_)=>
        {
            using var dialog=new SelectFolderDialog{Title="选择 PSD 输出文件夹",Directory=folder.Text};
            if(dialog.ShowDialog(this)==DialogResult.Ok)folder.Text=dialog.Directory;
        };
        options.AddRow(new Label{Text="输出宽度"},width,new Label{Text="高度"},height,null);
        options.AddRow(new Label{Text="预览模式"},modes,refreshPreview,null);
        previewHost.Add(preview,0,0);
        previewHost.SizeChanged+=(_,_)=>Guard(FitPreview);
        var right=new DynamicLayout{Spacing=new(8,8)};right.AddRow(options);right.AddRow(frameLabel);
        right.Add(previewHost,true,true);
        right.AddRow(new Label{Text="可旋转预览；导出以保存的 Named View 为准。"});
        var splitter=new Splitter{Orientation=Orientation.Horizontal,Panel1=left,Panel2=right,Position=465,FixedPanel=SplitterFixedPanel.Panel1};
        var bottom=outputOptions;
        bottom.AddRow(new StackLayout{Orientation=Orientation.Horizontal,Spacing=24,Items={material,shadow}});
        bottom.AddRow(new Label{Text="材质通道沿用图层颜色分层；预览显示模式不改变导出通道。"});
        browse.Width=125;
        bottom.AddRow(new TableLayout{Spacing=new(8,6),Rows={new TableRow(
            new TableCell(new Label{Text="输出文件夹"},false),new TableCell(folder,true),new TableCell(browse,false))}});
        var actions=new DynamicLayout{Spacing=new(8,8)};actions.AddRow(status,null,cancel,export);
        var layout=new DynamicLayout{Spacing=new(10,10)};
        layout.AddRow(new Label{Text="Named View → 通道选择 → 分层 PSD",Font=new Font(SystemFont.Bold,13)});
        layout.Add(splitter,true,true);layout.AddRow(bottom);layout.AddRow(progress);layout.AddRow(actions);layout.AddRow(log);
        Content=layout;
        export.Click+=async(_,_)=>await StartExport();
        cancel.Click+=(_,_)=>{cancellation?.Cancel();status.Text="正在取消，已完成的文件会保留…";};
        Shown+=(_,_)=>{shown=true;Guard(RefreshPreview);};
        Closing+=(_,e)=>{if(busy&&!documentClosed){cancellation?.Cancel();e.Cancel=true;status.Text="正在取消，请稍候再关闭。";}};
        Closed+=(_,_)=>{RhinoDoc.CloseDocument-=OnDocumentClosed;cancellation?.Dispose();};
        RhinoDoc.CloseDocument+=OnDocumentClosed;
        RefreshNamedViews();
    }
    private void OnDocumentClosed(object? sender,DocumentEventArgs e)
    {if(e.Document.RuntimeSerialNumber==document){documentClosed=true;cancellation?.Cancel();Close();}}
    private void Guard(Action action)
    {try{action();}catch(Exception ex){status.Text=ex.Message;}}
    public void RefreshNamedViews()
    {
        if(busy)return;
        var selected=Selected?.Id;var old=rows.ToDictionary(r=>r.Id);
        var views=NamedViewExportService.List(Doc);rows.Clear();
        foreach(var v in views)
        {
            var row=old.GetValueOrDefault(v.Id)??new(){Id=v.Id,Width=v.Width,Height=v.Height};
            row.Name=v.Name;rows.Add(row);
        }
        grid.ReloadData(Enumerable.Range(0,rows.Count));
        grid.SelectedRow=rows.Count==0?-1:Math.Max(0,rows.ToList().FindIndex(r=>r.Id==selected));
        BindSelection();status.Text=rows.Count==0?"没有 Named View，请先在 Rhino 中保存命名视图。":$"已读取 {rows.Count} 个 Named View";
    }
    public void SelectNamedView(Guid id)
    {grid.SelectedRow=rows.ToList().FindIndex(r=>r.Id==id);BindSelection();}
    private void BindSelection()
    {
        binding=true;
        try
        {
            options.Enabled=Selected is not null&&!busy;
            if(Selected is {} row){width.Value=row.Width;height.Value=row.Height;modes.SelectedKey=row.Mode.ToString();}
        }
        finally{binding=false;}
        if(shown&&!busy)Guard(RefreshPreview);
    }
    private void UpdateSize()
    {
        if(binding||busy||Selected is not {} row)return;
        row.Width=(int)width.Value;row.Height=(int)height.Value;grid.ReloadData(Enumerable.Range(0,rows.Count));
        Guard(RefreshPreview);
    }
    private void FitPreview()
    {
        if(!shown||busy||Selected is not {} row)return;
        int maxW=Math.Max(64,previewHost.Width-16),maxH=Math.Max(64,previewHost.Height-16);
        double ratio=(double)row.Width/row.Height;
        int w=Math.Min(maxW,(int)Math.Round(maxH*ratio)),h=(int)Math.Round(w/ratio);
        preview.Size=new(Math.Max(32,w),Math.Max(32,h));
        previewHost.Move(preview,(previewHost.Width-preview.Width)/2,(previewHost.Height-preview.Height)/2);
    }
    public void RefreshPreview()
    {
        if(!shown||busy||Selected is not {} row)return;
        NamedViewExportService.RequireActive(Doc);NamedViewExportService.ValidateSize(row.Width,row.Height);
        FitPreview();
        NamedViewExportService.ApplyCamera(Doc,row.Id,preview.Viewport,row.Width,row.Height);
        preview.Viewport.DisplayMode=DisplayModeDescription.GetDisplayMode(row.Mode)??throw new InvalidOperationException("显示模式已删除，请刷新列表。");
        preview.Viewport.ConstructionGridVisible=false;preview.Viewport.ConstructionAxesVisible=false;preview.Viewport.WorldAxesVisible=false;
        preview.Refresh();frameLabel.Text=$"{row.Name}  ·  {row.Width} × {row.Height} px  ·  {modes.SelectedValue}";
    }
    public void CapturePreview(string path)
    {
        RefreshPreview();
        if(!Path.IsPathFullyQualified(path)||!path.EndsWith(".png",StringComparison.OrdinalIgnoreCase))throw new ArgumentException("预览路径需为绝对 .png 路径。");
        using var bitmap=DisplayPipeline.DrawToBitmap(preview.Viewport,Math.Max(64,preview.Width),Math.Max(64,preview.Height))
            ??throw new InvalidOperationException("Rhino 暂未生成预览，请刷新后重试。");
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);bitmap.Save(path,System.Drawing.Imaging.ImageFormat.Png);
    }
    private FileCollision ResolveCollision(string path)
    {
        var answer=MessageBox.Show(this,$"文件已存在：\n{path}\n\n是否覆盖？\n选择“否”将自动添加 001、002…；取消会中止本次批量导出。",
            "PSD 文件重名",MessageBoxButtons.YesNoCancel,MessageBoxType.Question);
        return answer==DialogResult.Yes?FileCollision.Overwrite:answer==DialogResult.No?FileCollision.Number:FileCollision.Cancel;
    }
    private void SetBusy(bool value)
    {
        busy=value;grid.Enabled=!value;options.Enabled=!value&&Selected is not null;viewTools.Enabled=!value;
        outputOptions.Enabled=!value;
        material.Enabled=shadow.Enabled=folder.Enabled=export.Enabled=!value;cancel.Enabled=value;
    }
    private static Task<T> OnUi<T>(Func<T> action)
    {
        if(!RhinoApp.InvokeRequired)
        {try{return Task.FromResult(action());}catch(Exception ex){return Task.FromException<T>(ex);}}
        var result=new TaskCompletionSource<T>(TaskCreationOptions.RunContinuationsAsynchronously);
        RhinoApp.InvokeOnUiThread(new Action(()=>{try{result.SetResult(action());}catch(Exception ex){result.SetException(ex);}}));
        return result.Task;
    }
    public async Task StartExport()
    {
        if(busy)return;
        try
        {
            var channels=new BatchChannels(material.Checked==true,shadow.Checked==true);
            var plan=NamedViewExportService.Plan(Doc,rows.Where(r=>r.Included).Select(r=>new NamedViewSpec(r.Id,r.Width,r.Height)).ToArray(),folder.Text,channels,ResolveCollision);
            SceneFlowPlugin.Instance.ExportDirectory=Path.GetFullPath(folder.Text);
            cancellation?.Dispose();cancellation=new();var token=cancellation.Token;var results=new List<BatchFileResult>();
            SetBusy(true);progress.MaxValue=Math.Max(1,plan.Length);progress.Value=0;log.Text="";
            try
            {
                foreach(var item in plan)
                {
                    token.ThrowIfCancellationRequested();
                    await OnUi(()=>{var row=rows.First(r=>r.Id==item.View.ViewId);row.Status="导出中…";grid.ReloadData(Enumerable.Range(0,rows.Count));status.Text=$"正在导出 {item.Name}";return true;});
                    BatchFileResult result;
                    try
                    {
                        using var prepared=await OnUi(()=>NamedViewExportService.Prepare(Doc,item,channels,token));
                        result=await Task.Run(()=>prepared.Write(token),token);
                    }
                    catch(OperationCanceledException){throw;}
                    catch(Exception ex){result=NamedViewExportService.Failure(item,ex);}
                    results.Add(result);
                    await OnUi(()=>
                    {
                        if(documentClosed||IsDisposed)return true;
                        rows.First(r=>r.Id==item.View.ViewId).Status=result.Ok?"已导出":"失败";grid.ReloadData(Enumerable.Range(0,rows.Count));
                        progress.Value=results.Count;log.Append((result.Ok?"✓ "+result.Path:"× "+result.Name+"："+result.Error)+Environment.NewLine,true);return true;
                    });
                }
                LastReport=new(results.ToArray(),false);
            }
            catch(OperationCanceledException){LastReport=new(results.ToArray(),true);}
            finally
            {
                await OnUi(()=>
                {
                    if(documentClosed||IsDisposed)return true;
                    foreach(var row in rows.Where(r=>r.Status=="导出中…"))row.Status="已取消";
                    SetBusy(false);grid.ReloadData(Enumerable.Range(0,rows.Count));
                    status.Text=$"{(LastReport?.Cancelled==true?"已取消":"批量完成")}：成功 {results.Count(r=>r.Ok)}，失败 {results.Count(r=>!r.Ok)}";return true;
                });
            }
        }
        catch(OperationCanceledException){status.Text="已取消，未写入文件。";}
        catch(Exception ex){if(!IsDisposed){status.Text=ex.Message;MessageBox.Show(this,ex.Message,"无法导出",MessageBoxType.Error);}}
    }
    public object GetState()=>new{document,busy,visible=Visible,selected=Selected?.Id,directory=folder.Text,status=status.Text,
        previewSize=new{width=preview.Width,height=preview.Height},previewMode=preview.Viewport.DisplayMode?.Id,
        channels=new{material=material.Checked==true,shadow=shadow.Checked==true},views=rows.ToArray(),
        displayModes=modes.Items.Select(m=>new{id=m.Key,name=m.Text}).ToArray(),lastReport=LastReport};
}
