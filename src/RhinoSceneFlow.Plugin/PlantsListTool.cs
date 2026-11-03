using Eto.Forms;
using Rhino;
using Rhino.DocObjects;

namespace RhinoSceneFlow.Plugin;

public sealed class PlantsListTool:Panel
{
    private readonly uint document;
    private readonly GridView list=new(){AllowMultipleSelection=true,Height=400};
    private readonly TextBox search=new(){PlaceholderText="搜索组合名称或图层"};
    private readonly Label status=new(){Wrap=WrapMode.Word};
    private readonly UITimer timer=new(){Interval=.35};
    private bool binding,stopped,selectionQueued;private string stamp="",selection="";
    private sealed record Row(Guid Id,string Name,string Layer,string Count,string Status);
    private RhinoDoc Doc=>RhinoDoc.FromRuntimeSerialNumber(document)??throw new InvalidOperationException("文档已关闭。");
    public PlantsListTool(RhinoDoc doc)
    {
        document=doc.RuntimeSerialNumber;
        list.Columns.Add(new GridColumn{HeaderText="名称",DataCell=new TextBoxCell{Binding=Binding.Property<Row,string>(r=>r.Name)},Width=150});
        list.Columns.Add(new GridColumn{HeaderText="图层",DataCell=new TextBoxCell{Binding=Binding.Property<Row,string>(r=>r.Layer)},Width=110});
        list.Columns.Add(new GridColumn{HeaderText="株数",DataCell=new TextBoxCell{Binding=Binding.Property<Row,string>(r=>r.Count)},Width=50});
        list.Columns.Add(new GridColumn{HeaderText="状态",DataCell=new TextBoxCell{Binding=Binding.Property<Row,string>(r=>r.Status)},Width=125});
        var menu=new ContextMenu();
        void Item(string label,Action action){var item=new ButtonMenuItem{Text=label};item.Click+=(_,_)=>Guard(action);menu.Items.Add(item);}
        Item("编辑组合",Edit);Item("定位到组合",Zoom);Item("修改名字…",Rename);Item("修改所在图层…",ChangeLayer);
        Item("显示",()=>Manage(visible:true));Item("隐藏",()=>Manage(visible:false));Item("锁定",()=>Manage(locked:true));Item("解锁",()=>Manage(locked:false));list.ContextMenu=menu;
        list.SelectionChanged+=(_,_)=>SelectionChanged();list.CellDoubleClick+=(_,e)=>Guard(()=>EditRow(e.Row));search.TextChanged+=(_,_)=>{stamp="";Refresh();};
        list.MouseDown+=(_,e)=>{if(e.Buttons.HasFlag(MouseButtons.Alternate)){var cell=list.GetCellAt(e.Location);if(cell?.RowIndex is int row&&row>=0&&!list.SelectedRows.Contains(row))list.SelectedRows=[row];}};
        var root=Ui.Layout();root.AddRow(ToolUi.Heading("Plants List"));root.AddRow(search);root.Add(list,true,true);root.AddRow(ToolUi.Row(Ui.Button("编辑组合",()=>Guard(Edit)),Ui.Button("结束单株编辑",PlantEditing.Exit),null));root.AddRow(status);Content=root;
        timer.Elapsed+=(_,_)=>Guard(Refresh);timer.Start();RhinoDoc.CloseDocument+=Closed;Refresh();
    }
    private Guid[] Selected()=>list.SelectedItems.Cast<Row>().Select(r=>r.Id).ToArray();
    private void SelectionChanged()
    {
        if(binding||stopped||selectionQueued)return;selectionQueued=true;
        // WPF may dispatch selection changes after DataStore/SelectedRows synchronization.
        // Read the final rows once on the next UI turn, rather than acting on an intermediate clear.
        Application.Instance.AsyncInvoke(()=>{selectionQueued=false;if(stopped||binding)return;Guard(()=>
        {var ids=Selected();if(PlantEditing.IsActive(document)&&ids.Length==0){stamp="";Refresh();return;}var native=PlantEditing.IsActive(document)?new[]{PlantEditing.Group!.Value}:Doc.Objects.GetSelectedObjects(false,false).Where(PlantGroups.IsGroup).Select(o=>o.Id).Order().ToArray();if(!ids.Order().SequenceEqual(native))Select(ids);});});
    }
    public void Select(Guid[] ids)
    {
        NamedViewExportService.RequireActive(Doc);var objects=ids.Select(id=>Doc.Objects.FindId(id)??throw new ArgumentException("组合已删除。")).ToArray();if(objects.Any(o=>!PlantGroups.IsGroup(o)))throw new ArgumentException("请选择植物组合。");
        if(PlantEditing.Group is Guid editing&&!ids.Contains(editing))PlantEditing.Exit();
        Doc.Objects.UnselectAll();if(!PlantEditing.IsActive(document))foreach(var obj in objects)if(obj.IsSelectable(true,false,false,false))Doc.Objects.Select(obj.Id);Doc.Views.Redraw();selection=Signature();
        binding=true;try{if(list.DataStore is IEnumerable<Row> rows)list.SelectedRows=rows.Select((r,i)=>(r,i)).Where(p=>ids.Contains(p.r.Id)).Select(p=>p.i).ToArray();}finally{binding=false;}
        status.Text=PlantEditing.IsActive(document)?"隔离编辑中 · 整个组合不会被移动或复制":objects.Any(o=>!o.IsSelectable(true,false,false,false))?"隐藏或锁定的组合可在右键菜单恢复。":"已选择 "+objects.Length+" 个组合";
    }
    private string Signature()=>PlantEditing.IsActive(document)?PlantEditing.Group.ToString()!:string.Join(";",Doc.Objects.GetSelectedObjects(false,false).Where(PlantGroups.IsGroup).Select(o=>o.Id).Order());
    internal void Refresh()
    {
        if(stopped||!Doc.IsAvailable||Doc.IsClosing||Doc.IsOpening||Doc.IsCreating||RhinoApp.InCommand>0)return;
        var rows=PlantGroups.Objects(Doc).Select(o=>new Row(o.Id,o.Name,Doc.Layers[o.Attributes.LayerIndex].FullPath,PlantGroups.Rows(o).Length.ToString(),(PlantEditing.IsEditing(document,o.Id)?"编辑中 ":"")+(o.IsHidden?"隐藏 ":"")+(o.IsLocked?"锁定 ":"")+(Doc.Layers[o.Attributes.LayerIndex].IsVisible?"":"图层隐藏 ")+(Doc.Layers[o.Attributes.LayerIndex].IsLocked?"图层锁定 ":"")+"自定义 "+PlantGroups.Read(o)!.Individuals.Length)).Where(r=>(r.Name+" "+r.Layer).Contains(search.Text??"",StringComparison.OrdinalIgnoreCase)).ToArray();
        string next=string.Join("|",rows.Select(r=>r.ToString()));string chosen=Signature();
        if(next!=stamp||chosen!=selection)
        {
            binding=true;try{var selected=chosen.Split(';').ToHashSet();if(next!=stamp)list.DataStore=rows;list.SelectedRows=rows.Select((r,i)=>(r,i)).Where(p=>selected.Contains(p.r.Id.ToString())).Select(p=>p.i).ToArray();stamp=next;selection=chosen;}finally{binding=false;}
        }
    }
    private void Edit(){var ids=Selected();if(ids.Length!=1)throw new ArgumentException("选择一个组合进入编辑。");PlantEditing.Enter(Doc,ids[0]);}
    private void EditRow(int index)
    {
        if(index<0||list.DataStore is not IEnumerable<Row> rows)return;var row=rows.ElementAtOrDefault(index);if(row==null)return;
        Select([row.Id]);PlantEditing.Enter(Doc,row.Id);
    }
    private void Zoom(){var boxes=Selected().Select(id=>Doc.Objects.FindId(id)!.Geometry.GetBoundingBox(true)).ToArray();if(boxes.Length==0)return;var box=boxes[0];foreach(var b in boxes.Skip(1))box.Union(b);Doc.Views.ActiveView.ActiveViewport.ZoomBoundingBox(box);Doc.Views.Redraw();}
    private string? Prompt(string title,string initial)
    {using var dialog=new Dialog<bool>{Title=title,Padding=12};var text=new TextBox{Text=initial,Width=280};var ok=new Button{Text="确定"};var cancel=new Button{Text="取消"};ok.Click+=(_,_)=>dialog.Close(true);cancel.Click+=(_,_)=>dialog.Close(false);var layout=Ui.Layout();layout.AddRow(text);layout.AddRow(ok,cancel);dialog.Content=layout;dialog.DefaultButton=ok;dialog.AbortButton=cancel;return dialog.ShowModal(this)?text.Text:null;}
    private void Rename(){var ids=Selected();if(ids.Length!=1)throw new ArgumentException("选择一个组合修改名字。");var value=Prompt("组合名称",Doc.Objects.FindId(ids[0])!.Name);if(value!=null)Manage(name:value);}
    private void ChangeLayer()
    {
        var layers=Doc.Layers.Where(l=>!l.IsDeleted).ToArray();using var dialog=new Dialog<bool>{Title="移动到图层",Padding=12};var choices=new DropDown{Width=280};foreach(var l in layers)choices.Items.Add(new ListItem{Key=l.Id.ToString(),Text=l.FullPath});if(layers.Length>0)choices.SelectedIndex=0;
        var ok=new Button{Text="确定"};var cancel=new Button{Text="取消"};ok.Click+=(_,_)=>dialog.Close(true);cancel.Click+=(_,_)=>dialog.Close(false);var layout=Ui.Layout();layout.AddRow(choices);layout.AddRow(ok,cancel);dialog.Content=layout;dialog.DefaultButton=ok;dialog.AbortButton=cancel;if(dialog.ShowModal(this)&&Guid.TryParse(choices.SelectedKey,out var layer))Manage(layer:layer);
    }
    private void Manage(string? name=null,Guid? layer=null,bool? visible=null,bool? locked=null){Manage(Doc,Selected(),name,layer,visible,locked);stamp="";Refresh();}
    public static object Manage(RhinoDoc doc,Guid[] ids,string? name=null,Guid? layer=null,bool? visible=null,bool? locked=null)
    {
        if(PlantEditing.IsActive(doc.RuntimeSerialNumber))throw new InvalidOperationException("请先完成或取消单株编辑，再管理组合。");
        NamedViewExportService.RequireActive(doc);if(ids.Length==0)throw new ArgumentException("先选择组合。");if(name!=null&&(string.IsNullOrWhiteSpace(name)||name.Length>200))throw new ArgumentException("组合名称需为 1–200 个字符。");
        var objects=ids.Select(id=>doc.Objects.FindId(id)??throw new ArgumentException("组合不存在。")).ToArray();if(objects.Any(o=>!PlantGroups.IsGroup(o)))throw new ArgumentException("不是植物组合。");var target=layer.HasValue?doc.Layers.FindId(layer.Value)??throw new ArgumentException("图层不存在。"):null;
        uint undo=doc.BeginUndoRecord("管理植物组合");try{foreach(var obj in objects)
        {
            var attrs=obj.Attributes.Duplicate();if(name!=null){var spec=PlantGroups.Read(obj)!;spec.Name=name;attrs.Name=name;attrs.SetUserString(PlantGroups.Key,MaterialService.Serialize(spec));}if(target!=null)attrs.LayerIndex=target.Index;
            if(visible.HasValue||locked.HasValue){bool hidden=visible.HasValue?!visible.Value:obj.IsHidden;bool isLocked=locked??(obj.IsLocked||obj.IsHidden&&obj.Attributes.GetUserString("SceneFlow.PlantHiddenLock")=="true");attrs.SetUserString("SceneFlow.PlantHiddenLock",isLocked?"true":"false");attrs.Mode=hidden?ObjectMode.Hidden:isLocked?ObjectMode.Locked:ObjectMode.Normal;}
            if(!doc.Objects.ModifyAttributes(obj.Id,attrs,true))throw new InvalidOperationException("无法修改组合。");
        }}finally{if(undo!=0)doc.EndUndoRecord(undo);}doc.Views.Redraw();return new{objects=ids};
    }
    public object State()=>new{document,selected=Selected(),editing=PlantEditing.State(),count=PlantGroups.Objects(Doc).Length};
    private void Guard(Action action){if(stopped)return;try{action();}catch(Exception e){status.Text=e.Message;}}
    private void Closed(object? s,DocumentEventArgs e){if(e.Document.RuntimeSerialNumber==document){stopped=true;timer.Stop();}}
    protected override void Dispose(bool disposing){if(disposing){stopped=true;timer.Stop();timer.Dispose();RhinoDoc.CloseDocument-=Closed;}base.Dispose(disposing);}
}
