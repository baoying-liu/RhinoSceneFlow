using System.Drawing;
using System.Text.Json;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Render;
using Rhino.Runtime;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class MappingSettings
{
    public string Mode { get; set; } = "auto";
    public string Alignment { get; set; } = "continuous";
    public string Axis { get; set; } = "auto";
    public double Rotation { get; set; }
    public double OffsetUMeters { get; set; }
    public double OffsetVMeters { get; set; }
    public double[] OriginMeters { get; set; } = [0,0,0];
    public bool Checker { get; set; }
    public void Validate()
    {
        if(Mode is not ("auto" or "plane" or "box" or "cylinder" or "xatlas")||Alignment is not ("continuous" or "object")||Axis is not ("auto" or "x" or "y" or "z"))throw new ArgumentException("无效的映射方式 / 对齐 / 轴向。");
        if(OriginMeters is null||OriginMeters.Length!=3||OriginMeters.Any(v=>!double.IsFinite(v))||!double.IsFinite(Rotation)||!double.IsFinite(OffsetUMeters)||!double.IsFinite(OffsetVMeters))throw new ArgumentException("映射参数必须是有限数值。");
    }
}
public sealed class MaterialBinding
{
    public Guid Asset { get; set; }
    public int Revision { get; set; }
    public MappingSettings Settings { get; set; } = new();
    public double UnitScale { get; set; }
    public double[] Bounds { get; set; } = [];
}
internal sealed class MaterialBackup
{
    public int MaterialSource { get; set; }
    public int MaterialIndex { get; set; }
    public Guid RenderMaterial { get; set; }
    public string? Mapping { get; set; }
    public double[] Transform { get; set; } = [];
    public string? Binding { get; set; }
    public string? WorldUv { get; set; }
}
internal sealed class LayerMaterialBackup
{
    public Guid RenderMaterial { get; set; }
    public int MaterialIndex { get; set; }
    public string? Binding { get; set; }
}

public static partial class MaterialService
{
    internal const string BindingKey="RhinoSceneFlow.Material",BackupKey="RhinoSceneFlow.MaterialBackup",LayerBackupKey="RhinoSceneFlow.LayerMaterialBackup";
    public static MaterialLibrary Library=>new(SceneFlowPlugin.Instance.MaterialDirectory);
    internal static string Serialize<T>(T value)=>JsonSerializer.Serialize(value,MaterialLibrary.Json);
    internal static T Deserialize<T>(string text)=>JsonSerializer.Deserialize<T>(text,MaterialLibrary.Json)??throw new InvalidDataException("无效的材质配置。");
    public static MaterialAsset Import(MaterialAsset descriptor,Dictionary<string,string> files)
    {
        ValidateImages(files);return Library.Import(descriptor,files);
    }
    internal static void ValidateImages(IReadOnlyDictionary<string,string> files)
    {
        foreach(var file in files.Values)
        {
            using var image=Image.FromFile(file);
            if(image.Width<2||image.Height<2||image.Width>8192||image.Height>8192||(long)image.Width*image.Height>67_108_864)throw new ArgumentException("贴图每边需为 2–8192 像素。");
        }
    }
    public static double UnitScale(RhinoDoc doc)
    {
        if(doc.ModelUnitSystem is UnitSystem.None or UnitSystem.CustomUnits)throw new NotSupportedException("请先设置模型为毫米、米、英尺等标准单位。");
        double scale=RhinoMath.UnitScale(UnitSystem.Meters,doc.ModelUnitSystem);
        if(!double.IsFinite(scale)||scale<=0)throw new ArgumentException("模型单位无效。");return scale;
    }
    private static RhinoObject[] Targets(RhinoDoc doc,Guid[]? objects,Guid[]? layers)
    {
        NamedViewExportService.RequireActive(doc);
        if((objects is null||objects.Length==0)==(layers is null||layers.Length==0))throw new ArgumentException("请指定对象或图层，二选一。");
        RhinoObject[] found;
        if(objects is {Length:>0})found=objects.Distinct().Select(id=>doc.Objects.FindId(id)??throw new ArgumentException("对象已删除："+id)).ToArray();
        else
        {
            var selected=layers!.Distinct().Select(id=>doc.Layers.FindId(id)??throw new ArgumentException("图层已删除："+id)).ToArray();
            if(selected.Any(l=>l.IsDeleted||l.IsReference))throw new ArgumentException("不能修改参考或已删除图层。");
            var indices=selected.Select(l=>l.Index).ToHashSet();found=doc.Objects.Where(o=>indices.Contains(o.Attributes.LayerIndex)).ToArray();
        }
        if(found.Length==0)throw new ArgumentException("目标中没有面对象。");
        if(found.Any(o=>o.IsLocked||o.IsReference||o.IsDeleted||o.Geometry is not (Brep or Surface or Mesh or Extrusion or SubD)))throw new NotSupportedException("请只选择可编辑的面 / 网格 / SubD；块、曲线、参考或锁定对象暂不支持。");
        return found;
    }
    public static object Apply(RhinoDoc doc,Guid assetId,Guid[]? objects,Guid[]? layers,MappingSettings settings,bool preview=false)
    {
        settings.Validate();double scale=UnitScale(doc);var asset=Library.Get(assetId);Library.Verify(asset);var targets=Targets(doc,objects,layers);
        using var plan=PlanUv(doc,targets,settings,false);
        var report=new{asset=asset.Id,revision=asset.Revision,preview,unit=doc.ModelUnitSystem.ToString(),modelUnitsPerMeter=scale,widthInModelUnits=asset.WidthMeters*scale,heightInModelUnits=asset.HeightMeters*scale,
            uvComputed=plan.Items.Count(t=>t.Mapping!=null),uvReused=plan.Items.Count(t=>t.Mapping==null),
            objects=plan.Items.Select(t=>new{id=t.Object.Id,mode=t.Record.Mode,willReplaceMapping=t.Mapping!=null,canRestore=t.Object.Attributes.GetUserString(BackupKey)!=null}).ToArray()};
        if(preview)return report;
        uint undo=doc.BeginUndoRecord("SceneFlow 应用材质 / 补算真实世界 UV");
        try
        {
            CommitUv(doc,plan);
            var material=DocumentMaterial(doc,asset,settings.Checker);
            if(layers is {Length:>0})foreach(var id in layers.Distinct())
            {
                var layer=doc.Layers.FindId(id)!;
                if(layer.GetUserString(LayerBackupKey)==null)layer.SetUserString(LayerBackupKey,Serialize(new LayerMaterialBackup{RenderMaterial=layer.RenderMaterial?.Id??Guid.Empty,MaterialIndex=layer.RenderMaterialIndex,Binding=layer.GetUserString(BindingKey)}));
                layer.RenderMaterial=material;layer.SetUserString(BindingKey,Serialize(new MaterialBinding{Asset=asset.Id,Revision=asset.Revision,Settings=MaterialLibrary.Clone(settings),UnitScale=scale}));
            }
            foreach(var item in plan.Items)
            {
                var obj=doc.Objects.FindId(item.Object.Id)!;var attrs=obj.Attributes.Duplicate();
                attrs.SetUserString(BindingKey,Serialize(new MaterialBinding{Asset=asset.Id,Revision=asset.Revision,Settings=item.Record.Settings,UnitScale=scale,Bounds=Bounds(obj)}));
                attrs.MaterialSource=layers is {Length:>0}?ObjectMaterialSource.MaterialFromLayer:ObjectMaterialSource.MaterialFromObject;
                if(!doc.Objects.ModifyAttributes(obj,attrs,true))throw new InvalidOperationException("无法修改对象属性。");
                if(layers is not {Length:>0}){var current=doc.Objects.FindId(obj.Id)!;current.RenderMaterial=material;current.CommitChanges();}
            }
        }
        finally{if(undo!=0)doc.EndUndoRecord(undo);}
        doc.Views.Redraw();return report;
    }
    public static object Restore(RhinoDoc doc,Guid[]? objects,Guid[]? layers)
    {
        var targets=Targets(doc,objects,layers);var records=targets.Select(o=>(Object:o,Backup:o.Attributes.GetUserString(BackupKey))).Where(t=>t.Backup!=null).Select(t=>(t.Object,Backup:Deserialize<MaterialBackup>(t.Backup!))).ToArray();
        uint undo=doc.BeginUndoRecord("SceneFlow 恢复原材质与映射");
        try
        {
            if(layers is {Length:>0})foreach(var id in layers.Distinct())
            {
                var layer=doc.Layers.FindId(id)!;string? text=layer.GetUserString(LayerBackupKey);if(text==null)continue;
                var old=Deserialize<LayerMaterialBackup>(text);if(old.RenderMaterial!=Guid.Empty)layer.RenderMaterial=doc.RenderMaterials.Find(old.RenderMaterial)??throw new InvalidOperationException("原图层材质已删除。");else layer.RenderMaterialIndex=old.MaterialIndex;
                layer.SetUserString(BindingKey,old.Binding);layer.SetUserString(LayerBackupKey,null);
            }
            foreach(var (obj,backup) in records)
            {
                using var map=backup.Mapping==null?null:Deserialize<MappingSnapshot>(backup.Mapping).Build();
                if(backup.RenderMaterial!=Guid.Empty){obj.RenderMaterial=doc.RenderMaterials.Find(backup.RenderMaterial)??throw new InvalidOperationException("原对象材质已删除。");obj.CommitChanges();}
                var attrs=doc.Objects.FindId(obj.Id)!.Attributes.Duplicate();attrs.MaterialSource=(ObjectMaterialSource)backup.MaterialSource;attrs.MaterialIndex=backup.MaterialIndex;attrs.SetUserString(BindingKey,backup.Binding);attrs.SetUserString(BackupKey,null);attrs.SetUserString(WorldUvKey,backup.WorldUv);
                if(!doc.Objects.ModifyAttributes(obj.Id,attrs,true))throw new InvalidOperationException("恢复对象属性失败。");
                doc.Objects.FindId(obj.Id)!.SetTextureMapping(1,map,FromArray(backup.Transform));
            }
        }
        finally{if(undo!=0)doc.EndUndoRecord(undo);}
        doc.Views.Redraw();return new{restored=records.Select(r=>r.Object.Id).ToArray()};
    }
    public static object Inspect(RhinoDoc doc,Guid[] objects)=>objects.Select(id=>
    {
        var o=doc.Objects.FindId(id)??throw new ArgumentException("对象不存在。");var text=o.Attributes.GetUserString(BindingKey);var b=text==null?null:Deserialize<MaterialBinding>(text);
        return new{id,binding=b,canRestore=o.Attributes.GetUserString(BackupKey)!=null,worldUv=UvStatus(doc,o),needsRemap=!UvValid(doc,o),materialSource=o.Attributes.MaterialSource.ToString(),renderMaterial=o.GetRenderMaterial(true)?.Id};
    }).ToArray();
    public static object Remap(RhinoDoc doc,Guid[] objects)
    {
        var targets=Targets(doc,objects,null);uint undo=doc.BeginUndoRecord("SceneFlow 重新计算真实世界 UV");
        try
        {
            // Preflight all targets before modifying any of them.
            var plans=new List<UvPlan>();
            try
            {
                foreach(var obj in targets){var record=ReadUv(obj);plans.Add(PlanUv(doc,[obj],record?.Settings??new MappingSettings(),true));}
                foreach(var plan in plans)CommitUv(doc,plan);
                doc.Views.Redraw();return new{remapped=targets.Select(o=>o.Id).ToArray()};
            }
            finally{foreach(var p in plans)p.Dispose();}
        }
        finally{if(undo!=0)doc.EndUndoRecord(undo);}
    }
    public static object SyncLayers(RhinoDoc doc,Guid[] layers)
    {
        NamedViewExportService.RequireActive(doc);
        var bindings=layers.Distinct().Select(id=>(Id:id,Binding:Deserialize<MaterialBinding>(doc.Layers.FindId(id)?.GetUserString(BindingKey)??throw new ArgumentException("图层尚未配置 SceneFlow 材质。")))).ToArray();
        foreach(var t in bindings){t.Binding.Settings.Validate();Library.Verify(Library.Get(t.Binding.Asset));Targets(doc,null,[t.Id]);}
        uint undo=doc.BeginUndoRecord("SceneFlow 同步图层材质与映射");
        try{return bindings.Select(t=>Apply(doc,t.Binding.Asset,null,[t.Id],t.Binding.Settings)).ToArray();}
        finally{if(undo!=0)doc.EndUndoRecord(undo);}
    }
    internal static (TextureMapping Mapping,string Mode) BuildMapping(RhinoObject obj,MaterialAsset asset,MappingSettings settings,double scale)
    {
        string mode=settings.Mode;using var brep=ToBrep(obj.Geometry);Plane? surfacePlane=null;Cylinder? cylinder=null;
        if(brep!=null)foreach(var face in brep.Faces){if(face.TryGetCylinder(out var c))cylinder??=c;if(brep.Faces.Count==1&&face.TryGetPlane(out var p))surfacePlane=p;}
        if(mode=="auto")mode=surfacePlane.HasValue?"plane":cylinder.HasValue?"cylinder":"box";
        var box=obj.Geometry.GetBoundingBox(true);var center=box.Center;
        var origin=settings.Alignment=="object"?box.Min:new Point3d(settings.OriginMeters[0]*scale,settings.OriginMeters[1]*scale,settings.OriginMeters[2]*scale);
        Vector3d normal=settings.Axis switch{"x"=>Vector3d.XAxis,"y"=>Vector3d.YAxis,"z"=>Vector3d.ZAxis,_=>mode=="cylinder"&&cylinder.HasValue?cylinder.Value.Axis:surfacePlane?.Normal??SmallestAxis(box)};
        if(mode=="plane"&&settings.Axis=="auto")
        {double dominant=Math.Abs(normal.Z)>=Math.Abs(normal.X)&&Math.Abs(normal.Z)>=Math.Abs(normal.Y)?normal.Z:Math.Abs(normal.X)>=Math.Abs(normal.Y)?normal.X:normal.Y;if(dominant<0)normal=-normal;}
        var plane=Frame(origin,normal);plane.Rotate(settings.Rotation*Math.PI/180,plane.ZAxis);
        plane.Origin+=plane.XAxis*settings.OffsetUMeters*scale+plane.YAxis*settings.OffsetVMeters*scale;
        double w=asset.WidthMeters*scale,h=asset.HeightMeters*scale;
        if(mode=="plane")return(TextureMapping.CreatePlaneMapping(plane,new(0,w),new(0,h),new(-1,1)),mode);
        if(mode=="box")
        {
            // Independent per-face projections keep rectangular tile dimensions on
            // every side. The original Brep/SubD is never replaced with this mesh.
            var frame=Frame(origin,settings.Axis=="auto"?Vector3d.ZAxis:normal);frame.Rotate(settings.Rotation*Math.PI/180,frame.ZAxis);
            using var mesh=MappingMesh(obj.Geometry,frame,w,h);
            var boxed=TextureMapping.CreateCustomMeshMapping(mesh);boxed.UvwTransform=Transform.Translation(-settings.OffsetUMeters/asset.WidthMeters,-settings.OffsetVMeters/asset.HeightMeters,0);return(boxed,mode);
        }
        if(!cylinder.HasValue)throw new NotSupportedException("圆柱映射需要可识别的圆柱曲面；自由曲面请选择箱式或平面。");
        var native=cylinder.Value;var axis=native.Axis;axis.Unitize();
        if(settings.Axis!="auto"&&Math.Abs(axis*normal)<.999999)throw new ArgumentException("所选轴与圆柱实际轴向不一致。");
        // Keep the actual cylinder center/radius; the offset controls its seam/height.
        var cp=Frame(native.CircleAt(0).Plane.Origin,axis);cp.Rotate(settings.Rotation*Math.PI/180,axis);
        double min=box.GetCorners().Min(p=>(p-cp.Origin)*axis),max=box.GetCorners().Max(p=>(p-cp.Origin)*axis);
        cp.Origin+=axis*(min+settings.OffsetVMeters*scale);double height=max-min;
        if(height<=1e-10)throw new ArgumentException("圆柱高度无效。");
        var map=TextureMapping.CreateCylinderMapping(new Cylinder(new Circle(cp,native.Radius),height),false);map.TextureSpace=TextureSpace.Single;
        map.UvwTransform=Transform.Translation(-settings.OffsetUMeters/asset.WidthMeters,0,0)*Transform.Scale(Plane.WorldXY,2*Math.PI*native.Radius/w,height/h,1);
        return(map,mode);
    }
    private static Plane Frame(Point3d origin,Vector3d normal)
    {
        normal.Unitize();var x=Math.Abs(normal*Vector3d.ZAxis)>.9?Vector3d.XAxis:Vector3d.CrossProduct(Vector3d.ZAxis,normal);x.Unitize();var y=Vector3d.CrossProduct(normal,x);y.Unitize();return new Plane(origin,x,y);
    }
    private static Vector3d SmallestAxis(BoundingBox b){var d=b.Diagonal;return d.X<d.Y&&d.X<d.Z?Vector3d.XAxis:d.Y<d.Z?Vector3d.YAxis:Vector3d.ZAxis;}
    private static Brep? ToBrep(GeometryBase g)=>g switch{Brep b=>b.DuplicateBrep(),Extrusion e=>e.ToBrep(),Surface s=>s.ToBrep(),SubD s=>s.ToBrep(),_=>null};
    private static Mesh MappingMesh(GeometryBase geometry,Plane frame,double w,double h)
    {
        using var brep=ToBrep(geometry);var meshes=geometry is Mesh m?[m.DuplicateMesh()]:brep!=null?Mesh.CreateFromBrep(brep,MeshingParameters.QualityRenderMesh):[];
        var output=new Mesh();var toLocal=Transform.PlaneToPlane(frame,Plane.WorldXY);
        try
        {
            foreach(var mesh in meshes)foreach(var face in mesh.Faces)
            {
                var points=(face.IsQuad?new[]{face.A,face.B,face.C,face.D}:new[]{face.A,face.B,face.C}).Select(i=>(Point3d)mesh.Vertices[i]).ToArray();
                var local=points.Select(p=>{p.Transform(toLocal);return p;}).ToArray();var n=Vector3d.CrossProduct(local[1]-local[0],local[2]-local[0]);
                int first=output.Vertices.Count;
                for(int i=0;i<points.Length;i++)
                {
                    output.Vertices.Add(points[i]);var p=local[i];double u,v;
                    if(Math.Abs(n.Z)>=Math.Abs(n.X)&&Math.Abs(n.Z)>=Math.Abs(n.Y)){u=p.X/w;v=p.Y/h;}
                    else if(Math.Abs(n.X)>=Math.Abs(n.Y)){u=p.Y/w;v=p.Z/h;}
                    else{u=p.X/w;v=p.Z/h;}
                    output.TextureCoordinates.Add((float)u,(float)v);
                }
                if(points.Length==4)output.Faces.AddFace(first,first+1,first+2,first+3);else output.Faces.AddFace(first,first+1,first+2);
            }
            output.Normals.ComputeNormals();if(!output.IsValid||output.Faces.Count==0)throw new ArgumentException("不能生成箱式映射网格。");return output;
        }
        catch{output.Dispose();throw;}
        finally{foreach(var mesh in meshes)mesh.Dispose();}
    }
    private static RenderMaterial DocumentMaterial(RhinoDoc doc,MaterialAsset asset,bool checker)
    {
        string name=$"SceneFlow_{asset.Id:N}_r{asset.Revision}_meter2"+(checker?"_checker":"");
        var existing=doc.RenderMaterials.FirstOrDefault(m=>m.Name==name);if(existing!=null)return existing;
        using var native=new Material{Name=name};native.ToPhysicallyBased();native.PhysicallyBased.Roughness=asset.Roughness;native.PhysicallyBased.Metallic=asset.Metallic;
        foreach(var (slot,_) in checker?new Dictionary<string,string>{{"baseColor",""}}:asset.Maps)
        {
            string path=checker?CheckerPath():Library.MapPath(asset,slot);
            using var texture=new Texture{FileName=path,Enabled=true,WrapU=TextureUvwWrapping.Repeat,WrapV=TextureUvwWrapping.Repeat,UvwTransform=Transform.Scale(Plane.WorldXY,1/asset.WidthMeters,1/asset.HeightMeters,1)};
            var type=slot switch{"roughness"=>TextureType.PBR_Roughness,"metallic"=>TextureType.PBR_Metallic,"normal"=>TextureType.Bump,_=>TextureType.PBR_BaseColor};
            native.PhysicallyBased.SetTexture(texture,type);
        }
        var render=RenderMaterial.FromMaterial(native,doc);render.Name=name;
        foreach(var slot in asset.Maps.Keys)
        {
            var usage=slot switch{"roughness"=>RenderMaterial.StandardChildSlots.PbrRoughness,"metallic"=>RenderMaterial.StandardChildSlots.PbrMetallic,"normal"=>RenderMaterial.StandardChildSlots.Bump,_=>RenderMaterial.StandardChildSlots.PbrBaseColor};
            var texture=render.GetTextureFromUsage(usage);if(texture!=null)
            {
                texture.SetMappingChannel(1,RenderContent.ChangeContexts.Program);
                texture.SetRepeatLocked(false,RenderContent.ChangeContexts.Program);
                texture.SetRepeat(new Vector3d(1/asset.WidthMeters,1/asset.HeightMeters,1),RenderContent.ChangeContexts.Program);
            }
        }
        if(!doc.RenderMaterials.Add(render)){render.Dispose();throw new InvalidOperationException("无法创建 Rhino 材质。");}return render;
    }
    public static string CheckerPath()
    {
        string path=Path.Combine(Library.Root,"checker.png");if(File.Exists(path))return path;Directory.CreateDirectory(Library.Root);
        using var b=new Bitmap(512,512);using var g=Graphics.FromImage(b);g.Clear(Color.White);
        using var dark=new SolidBrush(Color.FromArgb(45,45,45));g.FillRectangle(dark,0,0,256,256);g.FillRectangle(dark,256,256,256,256);
        using var font=new System.Drawing.Font("Arial",18);g.DrawString("U 0..1 / V 0..1",font,Brushes.Red,8,8);g.DrawLine(Pens.Red,8,45,225,45);b.Save(path,System.Drawing.Imaging.ImageFormat.Png);return path;
    }
    private static double[] Bounds(RhinoObject obj){var b=obj.Geometry.GetBoundingBox(true);return [b.Min.X,b.Min.Y,b.Min.Z,b.Max.X,b.Max.Y,b.Max.Z];}
    private static double[] ToArray(Transform t)=>Enumerable.Range(0,16).Select(i=>t[i/4,i%4]).ToArray();
    private static Transform FromArray(double[] data){if(data.Length!=16)return Transform.Identity;var t=Transform.Identity;for(int i=0;i<16;i++)t[i/4,i%4]=data[i];return t;}
}
