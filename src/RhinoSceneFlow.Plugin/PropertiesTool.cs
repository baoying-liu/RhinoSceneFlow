using Eto.Forms;
using Rhino;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class PropertiesTool:Panel
{
    private readonly uint document;
    private readonly Panel body=new();
    private readonly Panel editHeader=new(){Visible=false};
    private readonly UiLabel title=new(){Wrap=WrapMode.Word,Tag="localized-context"},status=new(){Wrap=WrapMode.Word},uvState=new(){Wrap=WrapMode.Word};
    private readonly UITimer timer=new(){Interval=.3};
    private readonly MaterialActionQueue actions;
    private readonly DropDown scope=new(){Width=100},mapping=new(){Width=100},species=new(){Width=100};
    private readonly UiTextBox materialName=new();
    private readonly NumericStepper roughness=Ui.Number(0,1,3),metallic=Ui.Number(0,1,3),width=Ui.Number(.001,1e8,3),height=Ui.Number(.001,1e8,3),scale=Ui.Number(.001,100,3);
    private readonly UiCheckBox custom=new(){Text="自定义 · 不随组合参数重新随机"},mirror=new(){Text="水平镜像"},resize=new(){Text="修改贴图实际尺寸（米）"};
    private readonly UiCheckBox editRoughness=new(){Text="粗糙度"},editMetallic=new(){Text="金属度"};
    private string originalName="";
    private Action? afterUv;private Guid[] pendingUv=[];
    private readonly Panel materialPanel=new(),individualPanel=new();
    private readonly Panel groupActions=new();
    private PlantTool? groupTool;
    private Guid[] selected=[];private string stamp="";private bool stopped,binding;
    private RhinoDoc Doc=>RhinoDoc.FromRuntimeSerialNumber(document)??throw new InvalidOperationException("文档已关闭。");
    public PropertiesTool(RhinoDoc doc)
    {
        document=doc.RuntimeSerialNumber;actions=new(document,(s,p)=>status.Text=s);
        foreach(var (key,label) in new[]{("material","所有相同材质"),("layer","所选物件所在图层"),("object","仅所选物体")})scope.Items.Add(new UiListItem{Key=key,Text=label});scope.SelectedKey="material";
        foreach(var (key,label) in new[]{("auto","自动"),("plane","平面"),("box","箱式"),("cylinder","圆柱"),("xatlas","复杂曲面 · xatlas")})mapping.Items.Add(new UiListItem{Key=key,Text=label});mapping.SelectedKey="auto";
        var uv=Ui.Layout();uv.AddRow(mapping);uv.AddRow(uvState);uv.AddRow(Ui.Button("更新真实尺寸 UV",()=>Guard(()=>{actions.Start(CurrentObjects(),null,new(){Mode=mapping.SelectedKey??"auto"},force:true);})));uv.AddRow(Ui.Button("取消后续步骤",()=>{afterUv=null;actions.Cancel();}));
        var material=Ui.Layout();material.AddRow(new UiLabel{Text="修改范围"});material.AddRow(scope);material.AddRow(new UiLabel{Text="材质名称（多个值时留空）"});material.AddRow(materialName);material.AddRow(ToolUi.Row(editRoughness,roughness,null));material.AddRow(ToolUi.Row(editMetallic,metallic,null));material.AddRow(resize);material.AddRow(ToolUi.Row(new UiLabel{Text="实际宽度 m"},width,null));material.AddRow(ToolUi.Row(new UiLabel{Text="实际高度 m"},height,null));material.AddRow(Ui.Button("应用材质修改",()=>Guard(ApplyMaterial)));material.AddRow(ToolUi.Help("仅应用勾选或修改的参数，只修改当前文件。缩小范围时自动隔离共享材质，库中素材保留；贴图通道可能覆盖对应常数参数。"));
        roughness.ValueChanged+=(_,_)=>{if(!binding)editRoughness.Checked=true;};metallic.ValueChanged+=(_,_)=>{if(!binding)editMetallic.Checked=true;};
        var ordinary=Ui.Layout();ordinary.AddRow(new UiExpander{Header="材质设置",Content=material,Expanded=true});ordinary.AddRow(new UiExpander{Header="UV 设置 · 默认自动",Content=uv,Expanded=false});ordinary.AddRow(null);materialPanel.Content=ToolUi.VerticalScroll(ordinary);
        var plant=Ui.Layout();plant.AddRow(custom);plant.AddRow(new UiLabel{Text="植物类型 · 更换时保留当前高度"});plant.AddRow(species);plant.AddRow(ToolUi.Row(new UiLabel{Text="相对素材大小"},scale,null));plant.AddRow(mirror);plant.AddRow(Ui.Button("保存单株设置",()=>Guard(ApplyIndividual)));var groupButtons=Ui.Layout();groupButtons.AddRow(Ui.Button("在视口中移动 · 吸附承载面",()=>Guard(()=>PlantEditing.Move(Doc))));groupButtons.AddRow(Ui.Button("复制此株",()=>Guard(()=>{PlantEditing.ApplyTransform(Doc,Rhino.Geometry.Transform.Identity,true);stamp="";})));groupButtons.AddRow(Ui.Button("恢复组合设置",()=>Guard(()=>{var (g,r)=Individual();PlantEditing.Modify(Doc,g,r,custom:false);stamp="";})));groupButtons.AddRow(Ui.Button("返回组合设置",()=>Guard(()=>{if(PlantEditing.Group is Guid g)PlantEditing.Enter(Doc,g);})));groupButtons.AddRow(Ui.Button("结束单株编辑",()=>{PlantEditing.Exit();stamp="";}));groupActions.Content=groupButtons;plant.AddRow(groupActions);plant.AddRow(null);individualPanel.Content=ToolUi.VerticalScroll(plant);
        var root=Ui.Layout();root.AddRow(ToolUi.Heading("当前选择的属性"));root.AddRow(title);root.AddRow(editHeader);root.Add(body,true,true);root.AddRow(status);Content=root;
        timer.Elapsed+=(_,_)=>Guard(Refresh);timer.Start();RhinoDoc.CloseDocument+=Closed;Refresh();
    }
    private Guid[] CurrentObjects(){var ids=ToolUi.Selection(Doc);if(ids.Length==0||ids.Any(id=>PlantService.IsPlant(Doc.Objects.FindId(id)!)))throw new ArgumentException("先选择普通物件。");return ids;}
    private (Guid Group,string Row) Individual(){if(PlantEditing.Group is not Guid g||PlantEditing.Individual is not string r)throw new ArgumentException("先选择组合中的单株。");return(g,r);}
    private void Refresh()
    {
        if(stopped||!Doc.IsAvailable||Doc.IsClosing||Doc.IsOpening||Doc.IsCreating||RhinoApp.InCommand>0)return;
        if(afterUv!=null&&!actions.Busy){var apply=afterUv;afterUv=null;if(pendingUv.All(id=>Doc.Objects.FindId(id) is {} o&&MaterialService.UvValid(Doc,o)))apply();else status.Text="UV 未完成，材质修改未应用。";}
        selected=PlantEditing.IsActive(document)&&PlantEditing.Group is Guid active&&Doc.Objects.FindId(active)!=null?[active]:ToolUi.Selection(Doc);string next=string.Join(";",selected.Order().Select(id=>{var o=Doc.Objects.FindId(id)!;var m=o.GetRenderMaterial(true);return id+":"+o.Name+":"+o.Attributes.LayerIndex+":"+o.Attributes.GetUserString(PlantGroups.Key)?.GetHashCode()+":"+m?.Id+":"+m?.Name+":"+m?.GetParameter("pbr-roughness")+":"+m?.GetParameter("pbr-metallic")+":"+(PlantGroups.IsGroup(o)?o.Geometry.UserDictionary.GetString(PlantGroups.RowsKey)?.GetHashCode():0); }))+"|"+PlantEditing.Group+"|"+PlantEditing.Individual;
        if(PlantEditing.Group is Guid eg&&(!selected.Contains(eg)||Doc.Objects.FindId(eg)==null)){PlantEditing.Exit();next+="exit";}
        if(next==stamp)return;stamp=next;binding=true;try
        {
            body.Content=null;var oldHeader=editHeader.Content;editHeader.Content=null;oldHeader?.Dispose();editHeader.Visible=false;if(selected.Length==0){title.Text="选择物件、植物组合或组合中的一株植物";return;}
            var objects=selected.Select(id=>Doc.Objects.FindId(id)!).ToArray();
            if(selected.Length==1&&PlantGroups.IsGroup(objects[0]))
            {
                editHeader.Visible=true;var id=selected[0];var editing=PlantEditing.IsEditing(document,id);var header=Ui.Layout();
                if(editing){header.AddRow(new UiLabel{Text="隔离编辑中 · 单击一株后拖动操作柄；Ctrl 拖动复制单株。外部物件与整个组合已临时锁定。",Wrap=WrapMode.Word});header.AddRow(ToolUi.Row(Ui.Button("完成并退出",()=>{PlantEditing.Exit();stamp="";}),Ui.Button("取消本次编辑",()=>{PlantEditing.Cancel();stamp="";}),null));}
                else header.AddRow(Ui.Button("进入单株编辑",()=>Guard(()=>{PlantEditing.Enter(Doc,id);stamp="";})));
                editHeader.Content=header;
                if(PlantEditing.Group==selected[0]&&PlantEditing.Individual is string rowId)
                {
                    var row=PlantGroups.Rows(objects[0]).FirstOrDefault(r=>r.Id==rowId);if(row==null){stamp="";title.Text="正在更新单株…";return;}
                    var spec=PlantGroups.Read(objects[0])!;title.Text=objects[0].Name+" · 单株";custom.Visible=groupActions.Visible=true;custom.Checked=spec.Individuals.Any(i=>i.Id==rowId);mirror.Checked=row.Mirror;scale.Value=row.Scale;
                    species.Items.Clear();foreach(var a in PlantService.Library.List())species.Items.Add(new UiListItem{Key=a.Id.ToString(),Text=a.Plant!.ScientificName+" · "+PlantNames.Display(a,PlantUiPreferences.Load().ResolvedLanguage)});species.SelectedKey=row.Asset.ToString();body.Content=individualPanel;
                }
                else if(editing){title.Text=objects[0].Name+" · 隔离编辑";body.Content=new UiLabel{Text="在视口中单击需要调整的植物。移动、缩放、镜像和复制只作用于这一株。整体布局参数请完成或取消后调整。",Wrap=WrapMode.Word};}
                else{title.Text=objects[0].Name+" · 组合参数";groupTool??=new PlantTool(Doc,true);body.Content=groupTool;}
            }
            else if(objects.Length==1&&PlantService.Read(objects[0]) is {} loose)
            {title.Text=objects[0].Name+" · 独立植物";custom.Visible=groupActions.Visible=false;scale.Value=loose.Scale;mirror.Checked=loose.Mirror;species.Items.Clear();foreach(var a in PlantService.Library.List())species.Items.Add(new UiListItem{Key=a.Id.ToString(),Text=a.Plant!.ScientificName+" · "+PlantNames.Display(a,PlantUiPreferences.Load().ResolvedLanguage)});species.SelectedKey=loose.Asset.ToString();body.Content=individualPanel;}
            else if(objects.Any(PlantService.IsPlant)){title.Text="请选择一个植物组合，或进入组合编辑后选择单株。";}
            else
            {
                title.Text=$"{objects.Length} 个物件 · 普通物件属性";var materials=objects.Select(o=>o.GetRenderMaterial(true)).ToArray();
                var names=materials.Select(m=>m?.Name??"").Distinct().ToArray();materialName.Text=originalName=names.Length==1?names[0]:"";editRoughness.Checked=editMetallic.Checked=false;
                var first=materials[0];using var native=first==null?null:new Rhino.DocObjects.Material(first.ToMaterial(Rhino.Render.RenderTexture.TextureGeneration.Allow));
                roughness.Value=native?.IsPhysicallyBased==true?native.PhysicallyBased.Roughness:0;metallic.Value=native?.IsPhysicallyBased==true?native.PhysicallyBased.Metallic:0;
                var texture=first?.GetTextureFromUsage(Rhino.Render.RenderMaterial.StandardChildSlots.PbrBaseColor);var repeat=texture?.GetRepeat();
                width.Value=repeat.HasValue&&repeat.Value.X>0?1/repeat.Value.X:1;height.Value=repeat.HasValue&&repeat.Value.Y>0?1/repeat.Value.Y:1;resize.Checked=false;
                mapping.SelectedKey="auto";uvState.Text=objects.All(o=>MaterialService.UvValid(Doc,o))?"真实尺寸 UV 有效":"应用材质前会自动补算缺失或失效的 UV";
                body.Content=materialPanel;
            }
        }finally{binding=false;}
    }
    private void ApplyMaterial()
    {
        var ids=CurrentObjects();if(actions.Busy)throw new ArgumentException("请先等待 UV 更新完成。");
        if(materialName.Text==originalName&&editRoughness.Checked!=true&&editMetallic.Checked!=true&&resize.Checked!=true)throw new ArgumentException("先修改材质参数。");
        string targetScope=scope.SelectedKey??"material";string? newName=materialName.Text==originalName||string.IsNullOrWhiteSpace(materialName.Text)?null:materialName.Text;double? newRoughness=editRoughness.Checked==true?roughness.Value:null,newMetallic=editMetallic.Checked==true?metallic.Value:null,newWidth=resize.Checked==true?width.Value:null,newHeight=resize.Checked==true?height.Value:null;
        void Apply(){SelectionProperties.Modify(Doc,ids,targetScope,newName,newRoughness,newMetallic,newWidth,newHeight);status.Text="材质修改已应用，可使用 Rhino 撤销。";stamp="";}
        var affected=SelectionProperties.Affected(Doc,ids,targetScope);if(affected.Any(id=>Doc.Objects.FindId(id)!.IsLocked))throw new ArgumentException("目标包含锁定物件，请先解锁。");
        if(affected.Any(id=>!MaterialService.UvValid(Doc,Doc.Objects.FindId(id)!))){pendingUv=affected;actions.Start(affected,null,new(){Mode="auto"});afterUv=Apply;status.Text="先准备真实尺寸 UV，再修改并应用材质…";}else Apply();
    }
    private void ApplyIndividual()
    {
        if(binding)return;
        var live=ToolUi.Selection(Doc);if(live.Length==1&&PlantService.Read(Doc.Objects.FindId(live[0])!) is {} loose){PlantEditing.ModifyLoose(Doc,live[0],Guid.TryParse(species.SelectedKey,out var next)&&next!=loose.Asset?next:null,Math.Abs(scale.Value-loose.Scale)>1e-8?scale.Value:null,mirror.Checked==true);stamp="";return;}
        var (g,r)=Individual();var obj=Doc.Objects.FindId(g)!;var old=PlantGroups.Rows(obj).First(p=>p.Id==r);
        if(custom.Checked!=true&&!PlantGroups.Read(obj)!.Individuals.Any(i=>i.Id==r))custom.Checked=true;
        Guid? asset=Guid.TryParse(species.SelectedKey,out var id)&&id!=old.Asset?id:null;
        // A type change preserves height unless the user also changed scale explicitly.
        double? size=Math.Abs(scale.Value-old.Scale)>1e-8?scale.Value:null;
        PlantEditing.Modify(Doc,g,r,custom.Checked==true,asset,size,mirror.Checked==true);stamp="";status.Text="已保存；自定义植物计入密度和间距。";
    }
    public object State()=>new{document,selection=selected,scope=scope.SelectedKey,editing=PlantEditing.State(),title=title.Text,editHeaderVisible=editHeader.Visible,status=status.Text,busy=actions.Busy};
    private void Guard(Action action){if(stopped)return;try{action();}catch(Exception e){status.Text=e.Message;}}
    private void Closed(object? s,DocumentEventArgs e){if(e.Document.RuntimeSerialNumber==document){stopped=true;timer.Stop();afterUv=null;actions.Cancel();}}
    protected override void Dispose(bool disposing){if(disposing){stopped=true;timer.Stop();timer.Dispose();RhinoDoc.CloseDocument-=Closed;actions.Dispose();body.Content=null;groupTool?.Dispose();materialPanel.Dispose();individualPanel.Dispose();}base.Dispose(disposing);}
}
