using System.Runtime.InteropServices;
using System.Text.Json;
using Rhino;
using Rhino.DocObjects;
using Rhino.DocObjects.Custom;
using Rhino.Geometry;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class PlantAttachment
{
    public string Id {get;set;}=Guid.NewGuid().ToString("N");
    public Guid Asset {get;set;}
    public double[] Position {get;set;}=[0,0,0];
    public int Face {get;set;}=-1;
    public double U {get;set;}
    public double V {get;set;}
    public int[] Vertices {get;set;}=[];
    public double[] Weights {get;set;}=[];
    public int VertexCount {get;set;}
    public int FaceCount {get;set;}
}
public sealed class PlantGroupSpec
{
    public int Version {get;set;}=1;
    public string Name {get;set;}="种植组合";
    public Guid Surface {get;set;}
    public PlantPaletteItem[] Palette {get;set;}=[];
    public Dictionary<Guid,PlantInstance> Assets {get;set;}=[];
    public PlantAttachment[] Manual {get;set;}=[];
    public PlantIndividual[] Individuals {get;set;}=[];
    public PlantEditLayout? EditLayout {get;set;}
    public PlantLayoutSettings Settings {get;set;}=new();
}
public sealed class PlantEditLayout
{
    public string Key {get;set;}="";
    public LayoutPlant[] Rows {get;set;}=[];
}
public sealed class PlantIndividual
{
    public string Id {get;set;}="";
    public string OriginalId {get;set;}="";
    public int OriginalSeed {get;set;}
    public bool WasManual {get;set;}
    public PlantAttachment Attachment {get;set;}=new();
    public double Scale {get;set;}=1;
    public bool Mirror {get;set;}
    public LayoutPlant? Original {get;set;}
}

// Native geometry transformations survive copy, undo and 3dm serialization without rewriting parameters.
[Guid("A1932AE6-085B-4B88-B11F-073D8D203D16")]
public sealed class PlantGroupTransform:UserData
{
    public override string Description=>"SceneFlow planting transform";
    public override bool ShouldWrite=>true;
    internal void Set(Transform value){Transform=value;}
    protected override bool Write(Rhino.FileIO.BinaryArchiveWriter a){a.WriteTransform(Transform);return true;}
    protected override bool Read(Rhino.FileIO.BinaryArchiveReader a){Transform=a.ReadTransform();return true;}
    protected override void OnDuplicate(UserData source){base.OnDuplicate(source);Transform=((PlantGroupTransform)source).Transform;}
}
public static class PlantGroups
{
    internal const string Key="RhinoSceneFlow.PlantGroup.v1",RowsKey="SceneFlow.PlantRows.v1";
    private sealed class Work
    {
        internal string Stamp="",Stage="等待计算";internal DateTime Changed;internal CancellationTokenSource? Cancel;internal Task<PlantLayoutResult>? Task;
        internal PlantGroupSpec? Spec;internal Transform Transform;internal double Units;internal string? Error;
    }
    private static readonly Dictionary<(uint,Guid),Work> work=[];
    private static readonly Eto.Forms.UITimer timer=new(){Interval=.35};
    internal static bool Picking=false;
    private static readonly Dictionary<uint,(PlantGroupSpec Spec,LayoutPlant[] Rows,string Config)> decoded=[];
    private static bool running;
    internal static void Start(){if(running)return;running=true;PlantParameterUndo.Start();timer.Elapsed+=Tick;RhinoDoc.SelectObjects+=Selected;timer.Start();}
    internal static void Stop(){if(!running)return;running=false;PlantParameterUndo.Stop();timer.Stop();timer.Elapsed-=Tick;RhinoDoc.SelectObjects-=Selected;foreach(var w in work.Values)w.Cancel?.Cancel();work.Clear();decoded.Clear();}
    private static void Selected(object? sender,RhinoObjectSelectionEventArgs e)
    {
        if(Picking||SceneFlowWorkspace.Hosts.ContainsKey("properties")||!e.RhinoObjects.Any(IsGroup))return;uint serial=e.Document.RuntimeSerialNumber;
        Eto.Forms.Application.Instance.AsyncInvoke(()=>{var doc=RhinoDoc.ActiveDoc;if(running&&doc?.RuntimeSerialNumber==serial&&doc.IsAvailable&&!doc.IsClosing)try{SceneFlowWorkspace.Open("properties");}catch(Exception ex){System.Diagnostics.Debug.WriteLine(ex.Message);}});
    }
    internal static void Close(uint doc){foreach(var key in work.Keys.Where(k=>k.Item1==doc).ToArray()){work[key].Cancel?.Cancel();work.Remove(key);}decoded.Clear();}
    public static PlantGroupSpec? Read(RhinoObject obj)=>obj.Attributes.GetUserString(Key) is string s?JsonSerializer.Deserialize<PlantGroupSpec>(s,MaterialLibrary.Json):null;
    internal static bool IsGroup(RhinoObject o)=>o.Attributes.GetUserString(Key)!=null;
    internal static Transform Matrix(RhinoObject obj)=>(obj.Geometry.UserData.Find(typeof(PlantGroupTransform)) as PlantGroupTransform)?.Transform??Transform.Identity;
    internal static string LayoutKey(RhinoDoc doc,RhinoObject obj,PlantGroupSpec spec)
    {
        string text=MaterialService.Serialize(new{spec.Surface,spec.Settings,spec.Palette,spec.Manual,geometry=doc.Objects.FindId(spec.Surface)?.Geometry.DataCRC(0),units=doc.ModelUnitSystem});
        return Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(text)));
    }
    internal static void FreezeLayout(RhinoDoc doc,RhinoObject obj,PlantGroupSpec spec)
    {
        string key=LayoutKey(doc,obj,spec);if(spec.EditLayout?.Key==key)return;
        if(!Matrix(obj).TryGetInverse(out var inverse))throw new ArgumentException("组合变换不可逆。");double unit=RhinoMath.UnitScale(doc.ModelUnitSystem,UnitSystem.Meters);
        var rows=Rows(obj).Select(r=>r with{Position=V(inverse*P(r.Position/unit),unit)}).ToList();
        foreach(var i in spec.Individuals)
        {
            var current=rows.FirstOrDefault(r=>r.Id==i.Id);rows.RemoveAll(r=>r.Id==i.Id);
            if((i.WasManual||i.OriginalSeed==spec.Settings.LayoutSeed)&&!rows.Any(r=>r.Id==i.OriginalId))
            {var original=i.Original??(current is null?null:current with{Id=i.OriginalId,Manual=i.WasManual});if(original!=null)rows.Add(original);}
        }
        spec.EditLayout=new(){Key=key,Rows=rows.ToArray()};
    }
    internal static bool CommitEdited(RhinoDoc doc,Guid id)
    {
        var obj=doc.Objects.FindId(id);if(obj==null)return false;var spec=Read(obj)!;
        if(spec.EditLayout is not {} frozen||frozen.Key!=LayoutKey(doc,obj,spec)||doc.Objects.FindId(spec.Surface) is not {} carrier)return false;
        // Individual edits already have a valid layout. Do not mesh the carrier, weld edges,
        // debounce, or run scatter again just to replace one member's pose.
        double units=RhinoMath.UnitScale(doc.ModelUnitSystem,UnitSystem.Meters);var matrix=Matrix(obj);
        var originals=spec.Individuals.Where(i=>i.WasManual||i.OriginalSeed==spec.Settings.LayoutSeed).Select(i=>i.OriginalId).ToHashSet();
        var custom=spec.Individuals.Select(i=>i.Id).ToHashSet();var rows=frozen.Rows.Where(r=>!originals.Contains(r.Id)&&!custom.Contains(r.Id)).ToList();
        foreach(var i in spec.Individuals)
        {
            var item=Resolve(i.Attachment,carrier.Geometry,units,doc.ModelAbsoluteTolerance);
            rows.Add(new(i.Id,item.Asset,item.Position,true,i.Scale,i.Mirror,item.Detached));
        }
        var transformed=rows.Select(p=>p with{Position=V(matrix*P(p.Position/units),units)}).ToArray();
        using var proxy=Proxy(spec,transformed,units,matrix);bool modified=doc.Modified,undo=doc.UndoRecordingEnabled;
        try{doc.UndoRecordingEnabled=false;if(!doc.Objects.Replace(id,(GeometryBase)proxy,true))throw new InvalidOperationException("无法立即更新单株显示。");}
        finally{doc.UndoRecordingEnabled=undo;doc.Modified=modified;}
        if(!work.TryGetValue((doc.RuntimeSerialNumber,id),out var w))work[(doc.RuntimeSerialNumber,id)]=w=new();
        w.Cancel?.Cancel();w.Cancel?.Dispose();w.Cancel=null;w.Task=null;w.Spec=spec;w.Units=units;w.Transform=matrix;
        w.Stamp=Stamp(doc,doc.Objects.FindId(id)!);w.Stage=$"{rows.Count} 株 · 单株已更新";w.Error=null;
        return true;
    }
    internal static RhinoObject[] Objects(RhinoDoc doc)=>doc.Objects.GetObjectList(new ObjectEnumeratorSettings{ObjectTypeFilter=ObjectType.Mesh,NormalObjects=true,LockedObjects=true,HiddenObjects=true}).Where(IsGroup).ToArray();
    private static string Stamp(RhinoDoc doc,RhinoObject obj)
    {
        var s=Read(obj)!;var source=doc.Objects.FindId(s.Surface);var t=Matrix(obj);
        return obj.Attributes.GetUserString(Key)+"|"+(source?.Geometry.DataCRC(0).ToString()??"missing")+"|"+doc.ModelUnitSystem+"|"+string.Join(",",Enumerable.Range(0,16).Select(i=>t[i/4,i%4].ToString("R",System.Globalization.CultureInfo.InvariantCulture)));
    }
    internal static Mesh MeshFor(GeometryBase geometry)
    {
        var result=new Mesh();
        if(geometry is Mesh m)result.Append(m);
        else
        {
            using var b=geometry switch{Brep brep=>brep.DuplicateBrep(),Extrusion e=>e.ToBrep(),Surface s=>s.ToBrep(),_=>throw new ArgumentException("承载区域需为 Brep、Surface 或 Mesh。")};
            foreach(var part in Mesh.CreateFromBrep(b,MeshingParameters.Default)??[]){result.Append(part);part.Dispose();}
        }
        result.Faces.ConvertQuadsToTriangles();if(result.Faces.Count==0||result.Faces.Count>2_000_000){result.Dispose();throw new ArgumentException("承载面无有效网格或超过 200 万面。");}return result;
    }
    private static Vec3 V(Point3d p,double unit)=>new(p.X*unit,p.Y*unit,p.Z*unit);
    private static Point3d P(Vec3 p)=>new(p.X,p.Y,p.Z);
    internal static PlantAttachment Attach(GeometryBase geometry,Point3d point,Guid asset)
    {
        var a=new PlantAttachment{Asset=asset};Point3d p;
        if(geometry is Brep b)
        {
            if(!b.ClosestPoint(point,out p,out var component,out double u,out double v,0,out _))throw new ArgumentException("无法附着到曲面。");
            a.VertexCount=b.Vertices.Count;a.FaceCount=b.Faces.Count;
            if(component.ComponentIndexType==ComponentIndexType.BrepFace){a.Face=component.Index;a.U=u;a.V=v;}
        }
        else if(geometry is Surface s){if(!s.ClosestPoint(point,out double u,out double v))throw new ArgumentException("无法附着到曲面。");p=s.PointAt(u,v);a.Face=0;a.U=u;a.V=v;}
        else if(geometry is Mesh m)
        {
            var mp=m.ClosestMeshPoint(point,0)??throw new ArgumentException("无法附着到网格。");p=mp.Point;var f=m.Faces[mp.FaceIndex];a.Face=mp.FaceIndex;a.Vertices=[f.A,f.B,f.C,f.D];a.Weights=mp.T;a.VertexCount=m.Vertices.Count;a.FaceCount=m.Faces.Count;
        }
        else if(geometry is Extrusion e){using var b2=e.ToBrep();return Attach(b2,point,asset);}
        else throw new ArgumentException("承载区域需为 Brep、Surface 或 Mesh。");
        a.Position=[p.X,p.Y,p.Z];return a;
    }
    private static LayoutManual Resolve(PlantAttachment a,GeometryBase? geometry,double units,double tolerance,Point3d? previous=null)
    {
        var old=previous??new Point3d(a.Position[0],a.Position[1],a.Position[2]);Point3d p=old;bool attached=false;
        if(geometry is Brep b&&a.FaceCount==b.Faces.Count&&a.VertexCount==b.Vertices.Count&&a.Face>=0&&a.Face<b.Faces.Count&&a.Vertices.Length==0)
        {var f=b.Faces[a.Face];if(f.Domain(0).IncludesParameter(a.U)&&f.Domain(1).IncludesParameter(a.V)&&f.IsPointOnFace(a.U,a.V)!=PointFaceRelation.Exterior){p=f.PointAt(a.U,a.V);attached=true;}}
        else if(geometry is Surface s&&s.Domain(0).IncludesParameter(a.U)&&s.Domain(1).IncludesParameter(a.V)){p=s.PointAt(a.U,a.V);attached=true;}
        else if(geometry is Mesh m&&a.VertexCount==m.Vertices.Count&&a.FaceCount==m.Faces.Count&&a.Face>=0&&a.Face<m.Faces.Count&&a.Vertices.Length==4)
        {var f=m.Faces[a.Face];if(a.Vertices.SequenceEqual(new[]{f.A,f.B,f.C,f.D})){p=Point3d.Origin;for(int i=0;i<4;i++)p+=(Vector3d)(Point3d)m.Vertices[a.Vertices[i]]*a.Weights[i];attached=true;}}
        // Changed topology: only reattach near the last known world location, never jump to an unrelated face.
        if(!attached&&geometry!=null)try{var near=Attach(geometry,old,a.Asset);var q=new Point3d(near.Position[0],near.Position[1],near.Position[2]);if(q.DistanceTo(old)<=Math.Max(tolerance*10,.05/units)){p=q;attached=true;}}catch(ArgumentException){}
        return new(a.Id,a.Asset,V(p,units),!attached);
    }
    private static void Launch(RhinoDoc doc,RhinoObject obj,Work w)
    {
        var spec=Read(obj)!;spec.Settings.Validate();w.Spec=spec;w.Transform=Matrix(obj);w.Units=RhinoMath.UnitScale(doc.ModelUnitSystem,UnitSystem.Meters);
        var source=doc.Objects.FindId(spec.Surface);LayoutTriangle[] triangles=[];LayoutEdge[] edges=[];
        if(source!=null)
        {
            using var mesh=MeshFor(source.Geometry);var vertices=mesh.Vertices.Select(p=>V(p,w.Units)).ToArray();triangles=mesh.Faces.Select(f=>new LayoutTriangle(vertices[f.A],vertices[f.B],vertices[f.C])).ToArray();
            if(spec.Settings.EdgeStrength>0)
            {
                // Brep face meshes are appended independently: weld coincident seam vertices before finding the exterior boundary.
                mesh.Vertices.CombineIdentical(true,true);mesh.Weld(Math.PI);
                edges=(mesh.GetNakedEdges()??[]).SelectMany(line=>Enumerable.Range(1,line.Count-1).Select(i=>new LayoutEdge(V(line[i-1],w.Units),V(line[i],w.Units)))).ToArray();
            }
        }
        var oldRows=Rows(obj).Where(p=>p.Manual).ToDictionary(p=>p.Id);w.Transform.TryGetInverse(out var inverse);
        var manual=spec.Manual.Where(a=>!spec.Individuals.Any(i=>i.WasManual&&i.OriginalId==a.Id)).Select(a=>Resolve(a,source?.Geometry,w.Units,doc.ModelAbsoluteTolerance,oldRows.TryGetValue(a.Id,out var old)?inverse*P(old.Position/w.Units):null))
            .Concat(spec.Individuals.Select(i=>Resolve(i.Attachment,source?.Geometry,w.Units,doc.ModelAbsoluteTolerance,oldRows.TryGetValue(i.Id,out var old)?inverse*P(old.Position/w.Units):null) with{Id=i.Id,CustomScale=i.Scale,CustomMirror=i.Mirror,SpacingMeters=spec.Assets[i.Attachment.Asset].SpacingMeters})).ToArray();
        var excluded=spec.Individuals.Where(i=>!i.WasManual&&i.OriginalSeed==spec.Settings.LayoutSeed).Select(i=>i.OriginalId).ToHashSet();
        if(source==null){w.Stage="承载面已删除；保留最后结果，请重新关联。";w.Error=null;return;}
        w.Cancel=new();var token=w.Cancel.Token;w.Stage="正在计算种植布局…";w.Error=null;
        if(spec.EditLayout is {} frozen&&frozen.Key==LayoutKey(doc,obj,spec))
        {
            var rows=frozen.Rows.ToList();foreach(var i in spec.Individuals)
            {
                rows.RemoveAll(r=>r.Id==i.Id||((i.WasManual||i.OriginalSeed==spec.Settings.LayoutSeed)&&r.Id==i.OriginalId));
                var item=manual.First(m=>m.Id==i.Id);rows.Add(new(i.Id,item.Asset,item.Position,true,i.Scale,i.Mirror,item.Detached));
            }
            double area=triangles.Sum(t=>(t.B-t.A).Cross(t.C-t.A).Length*.5);int target=(int)Math.Round(area*spec.Settings.Density);
            w.Task=System.Threading.Tasks.Task.FromResult(new PlantLayoutResult(rows.ToArray(),target,0,rows.Count<target,area));
        }
        else w.Task=System.Threading.Tasks.Task.Run(()=>PlantLayout.Generate(triangles,edges,spec.Palette,manual,spec.Settings,token,excluded),token);
    }
    private static void Tick(object? sender,EventArgs e)
    {
        if(!running||Picking)return;var doc=RhinoDoc.ActiveDoc;if(doc==null||!doc.IsAvailable||doc.IsClosing||doc.IsOpening||RhinoApp.InCommand>0)return;
        var live=Objects(doc);var ids=live.Select(o=>o.Id).ToHashSet();foreach(var key in work.Keys.Where(k=>k.Item1==doc.RuntimeSerialNumber&&!ids.Contains(k.Item2)).ToArray()){work[key].Cancel?.Cancel();work.Remove(key);}
        foreach(var obj in live)
        {
            var key=(doc.RuntimeSerialNumber,obj.Id);if(!work.TryGetValue(key,out var w))work[key]=w=new();
            try
            {
                string stamp=Stamp(doc,obj);if(w.Stamp!=stamp){w.Cancel?.Cancel();w.Task=null;w.Cancel?.Dispose();w.Cancel=null;w.Stamp=stamp;w.Changed=DateTime.UtcNow;w.Error=null;w.Stage="等待曲面稳定…";continue;}
                if(w.Task is {IsCompleted:true} task)
                {
                    w.Task=null;if(task.IsCanceled)continue;if(task.IsFaulted)throw task.Exception!.GetBaseException();
                    var result=task.Result;var transformed=result.Plants.Select(p=>p with{Position=V(w.Transform*P(p.Position/w.Units),w.Units)}).ToArray();
                    using var proxy=Proxy(w.Spec!,transformed,w.Units,w.Transform);bool modified=doc.Modified,undo=doc.UndoRecordingEnabled;
                    // Derived geometry must refresh while the root remains locked for isolated editing.
                    try{doc.UndoRecordingEnabled=false;if(!doc.Objects.Replace(obj.Id,(GeometryBase)proxy,true))throw new InvalidOperationException("无法更新种植显示。");}
                    finally{doc.UndoRecordingEnabled=undo;doc.Modified=modified;}
                    w.Stage=$"{result.Plants.Length} 株 · 手工 {result.Plants.Count(p=>p.Manual)} · 目标 {result.Target}"+(result.Limited?" · 间距／边缘限制未填满":"")+(result.Plants.Any(p=>p.Detached)?" · 存在待重新附着的手工植物":"");w.Cancel?.Dispose();w.Cancel=null;doc.Views.Redraw();
                }
                else if(w.Task==null&&w.Cancel==null&&w.Stage=="等待曲面稳定…"&&(DateTime.UtcNow-w.Changed).TotalSeconds>.45&&work.Values.Count(v=>v.Task is {IsCompleted:false})<2)Launch(doc,obj,w);
            }
            catch(Exception ex){w.Stage="计算失败："+ex.Message;w.Error=ex.Message;w.Task=null;w.Cancel?.Dispose();w.Cancel=null;}
        }
    }
    private static Mesh Proxy(PlantGroupSpec spec,LayoutPlant[] rows,double units,Transform matrix)
    {
        var xs=new Vector3d(1,0,0);xs.Transform(matrix);var ys=new Vector3d(0,1,0);ys.Transform(matrix);var zs=new Vector3d(0,0,1);zs.Transform(matrix);double widthScale=Math.Sqrt(xs.Length*ys.Length),heightScale=zs.Length;
        var mesh=new Mesh();foreach(var row in rows)
        {
            var a=spec.Assets[row.Asset];var p=P(row.Position/units);double h=a.HeightMeters*row.Scale/units*heightScale,r=a.WidthMeters*row.Scale/units*.5*widthScale;int v=mesh.Vertices.Count;
            mesh.Vertices.Add(p.X-r,p.Y,p.Z);mesh.Vertices.Add(p.X+r,p.Y,p.Z);mesh.Vertices.Add(p.X+r,p.Y,p.Z+h);mesh.Vertices.Add(p.X-r,p.Y,p.Z+h);mesh.Faces.AddFace(v,v+1,v+2,v+3);
            v=mesh.Vertices.Count;mesh.Vertices.Add(p.X,p.Y-r,p.Z);mesh.Vertices.Add(p.X,p.Y+r,p.Z);mesh.Vertices.Add(p.X,p.Y+r,p.Z+h);mesh.Vertices.Add(p.X,p.Y-r,p.Z+h);mesh.Faces.AddFace(v,v+1,v+2,v+3);
        }
        if(mesh.Faces.Count==0){mesh.Vertices.Add(0,0,0);mesh.Vertices.Add(.001,0,0);mesh.Vertices.Add(0,.001,0);mesh.Faces.AddFace(0,1,2);}
        mesh.Normals.ComputeNormals();mesh.UserDictionary.Set(RowsKey,JsonSerializer.Serialize(rows,MaterialLibrary.Json));var data=new PlantGroupTransform();mesh.UserData.Add(data);data.Set(matrix);return mesh;
    }
    private static (PlantGroupSpec Spec,LayoutPlant[] Rows) Decoded(RhinoObject obj)
    {
        string config=obj.Attributes.GetUserString(Key)!;if(decoded.TryGetValue(obj.RuntimeSerialNumber,out var value)&&value.Config==config)return(value.Spec,value.Rows);
        if(decoded.Count>64)decoded.Clear();var rows=obj.Geometry.UserDictionary.GetString(RowsKey);
        value=(Read(obj)!,string.IsNullOrEmpty(rows)?[]:JsonSerializer.Deserialize<LayoutPlant[]>(rows,MaterialLibrary.Json)??[],config);decoded[obj.RuntimeSerialNumber]=value;return(value.Spec,value.Rows);
    }
    internal static LayoutPlant[] Rows(RhinoObject obj)=>Decoded(obj).Rows;
    internal static bool IsBusy(RhinoDoc doc,Guid id)=>work.TryGetValue((doc.RuntimeSerialNumber,id),out var w)&&(w.Task!=null||w.Stage=="等待曲面稳定…");
    internal static void RequireReady(RhinoDoc doc,RhinoObject obj)
    {
        if(doc.Objects.FindId(Read(obj)!.Surface)==null)return;
        if(!work.TryGetValue((doc.RuntimeSerialNumber,obj.Id),out var w)||w.Stamp!=Stamp(doc,obj)||IsBusy(doc,obj.Id))throw new InvalidOperationException("种植布局正在更新，请计算完成后再导出。");
        if(w.Error!=null)throw new InvalidOperationException(w.Error);
    }
    public static Guid Create(RhinoDoc doc,PlantGroupSpec spec)
    {
        NamedViewExportService.RequireActive(doc);Hydrate(spec);if(doc.Objects.FindId(spec.Surface)==null)throw new ArgumentException("先选择承载面。");using var check=MeshFor(doc.Objects.FindId(spec.Surface).Geometry);spec.Settings.Validate();
        using var mesh=Proxy(spec,[],RhinoMath.UnitScale(doc.ModelUnitSystem,UnitSystem.Meters),Transform.Identity);var attrs=new ObjectAttributes{Name=spec.Name};attrs.SetUserString(Key,JsonSerializer.Serialize(spec,MaterialLibrary.Json));uint undo=doc.BeginUndoRecord("创建种植组合");Guid id;
        try{id=doc.Objects.AddMesh(mesh,attrs);if(id==Guid.Empty)throw new InvalidOperationException("无法创建种植对象。");}finally{if(undo!=0)doc.EndUndoRecord(undo);}return id;
    }
    private static void Hydrate(PlantGroupSpec spec)
    {
        spec.Settings.Validate();if(spec.Manual.Length>10000||spec.Manual.Select(m=>m.Id).Distinct().Count()!=spec.Manual.Length||spec.Manual.Any(m=>string.IsNullOrWhiteSpace(m.Id)||m.Id.Length>80||m.Position.Length!=3||m.Position.Any(v=>!double.IsFinite(v))))throw new ArgumentException("手工种植数量或坐标无效。");
        if(spec.Individuals.Length>10000||spec.Individuals.Select(i=>i.Id).Distinct().Count()!=spec.Individuals.Length||spec.Individuals.Any(i=>string.IsNullOrWhiteSpace(i.Id)||i.Id.Length>80||i.Attachment.Id!=i.Id||!double.IsFinite(i.Scale)||i.Scale<=0||i.Scale>100||i.Attachment.Position.Length!=3||i.Attachment.Position.Any(v=>!double.IsFinite(v))))throw new ArgumentException("单株自定义设置无效。");
        spec.Assets.Clear();foreach(var assetId in spec.Palette.Select(p=>p.Asset).Concat(spec.Individuals.Select(i=>i.Attachment.Asset)).Distinct())
        {var a=PlantService.Library.Get(assetId);if(a.Plant==null)throw new ArgumentException("植物组合包含非植物素材。");PlantService.Library.Verify(a);spec.Assets[assetId]=new(){Asset=a.Id,Image=PlantService.Library.MapPath(a,"baseColor"),Sha256=a.Sha256["baseColor"],ScientificName=a.Plant.ScientificName,WidthMeters=a.WidthMeters,HeightMeters=a.HeightMeters,AnchorU=a.Plant.AnchorU,AnchorV=a.Plant.AnchorV,SpacingMeters=a.Plant.SpacingMeters};}
        if(spec.Palette.Length is <1 or >64||spec.Palette.Select(p=>p.Asset).Distinct().Count()!=spec.Palette.Length||spec.Palette.Any(p=>!double.IsFinite(p.Weight)||p.Weight<=0||!double.IsFinite(p.SpacingMeters)||p.SpacingMeters<0||p.SpacingMeters>1000)||spec.Manual.Any(m=>!spec.Palette.Any(p=>p.Asset==m.Asset)))throw new ArgumentException("植物组合的比重、间距或手工植物引用无效。");
    }
    public static void Update(RhinoDoc doc,Guid id,PlantGroupSpec spec)
    {
        if(PlantEditing.IsEditing(doc.RuntimeSerialNumber,id)&&!PlantEditing.Applying)throw new InvalidOperationException("请先完成或取消单株编辑，再修改整体组合。");
        NamedViewExportService.RequireActive(doc);var obj=doc.Objects.FindId(id)??throw new ArgumentException("种植对象已删除。");if(!IsGroup(obj))throw new ArgumentException("不是种植组合。");Hydrate(spec);
        if(Read(obj)!.Surface!=spec.Surface)
        {
            var carrier=doc.Objects.FindId(spec.Surface)??throw new ArgumentException("新承载面不存在。");using var check=MeshFor(carrier.Geometry);var rows=Rows(obj).ToDictionary(r=>r.Id);Matrix(obj).TryGetInverse(out var inverse);double unit=RhinoMath.UnitScale(doc.ModelUnitSystem,UnitSystem.Meters);
            PlantAttachment Reattach(PlantAttachment a){var p=rows.TryGetValue(a.Id,out var row)?inverse*P(row.Position/unit):new Point3d(a.Position[0],a.Position[1],a.Position[2]);var next=Attach(carrier.Geometry,p,a.Asset);next.Id=a.Id;return next;}
            spec.Manual=spec.Manual.Select(Reattach).ToArray();foreach(var individual in spec.Individuals)individual.Attachment=Reattach(individual.Attachment);
        }
        var attrs=obj.Attributes.Duplicate();attrs.Name=spec.Name;attrs.SetUserString(Key,JsonSerializer.Serialize(spec,MaterialLibrary.Json));uint undo=doc.BeginUndoRecord("修改种植参数");try{PlantParameterUndo.Record(doc,obj,attrs.GetUserString(Key)!,attrs.Name);if(!doc.Objects.ModifyAttributes(id,attrs,true))throw new InvalidOperationException("无法保存种植参数。");}finally{if(undo!=0)doc.EndUndoRecord(undo);}
    }
    public static void AddManual(RhinoDoc doc,Guid id,Guid asset,Point3d point)
    {
        var obj=doc.Objects.FindId(id)??throw new ArgumentException("种植对象已删除。");var spec=Read(obj)??throw new ArgumentException("不是种植组合。");var source=doc.Objects.FindId(spec.Surface)??throw new ArgumentException("承载面已删除，请先重新关联。");
        var matrix=Matrix(obj);if(!matrix.TryGetInverse(out var inverse))throw new ArgumentException("种植对象变换不可逆。");var attachment=Attach(source.Geometry,inverse*point,asset);spec.Manual=[..spec.Manual,attachment];Update(doc,id,spec);
        // Immediate preview for a continuous picking session; the background layout runs after Esc.
        var p=matrix*new Point3d(attachment.Position[0],attachment.Position[1],attachment.Position[2]);double units=RhinoMath.UnitScale(doc.ModelUnitSystem,UnitSystem.Meters);
        var row=new LayoutPlant(attachment.Id,asset,V(p,units),true,spec.Settings.MinScale+PlantLayout.Random(attachment.Id,spec.Settings.SizeSeed)*(spec.Settings.MaxScale-spec.Settings.MinScale),spec.Settings.Mirror&&PlantLayout.Random(attachment.Id,spec.Settings.MirrorSeed)<.5);
        using var proxy=Proxy(spec,[..Rows(obj),row],units,matrix);bool undo=doc.UndoRecordingEnabled;try{doc.UndoRecordingEnabled=false;doc.Objects.Replace(id,proxy);}finally{doc.UndoRecordingEnabled=undo;}doc.Views.Redraw();
    }
    public static object State(RhinoDoc doc,Guid id)
    {
        var obj=doc.Objects.FindId(id)??throw new ArgumentException("种植对象已删除。");var spec=Read(obj)??throw new ArgumentException("不是种植组合。");work.TryGetValue((doc.RuntimeSerialNumber,id),out var w);var rows=Rows(obj);
        return new{id,spec,count=rows.Length,manual=rows.Count(r=>r.Manual),detached=rows.Count(r=>r.Detached),busy=w==null||w.Stamp!=Stamp(doc,obj)||w.Task!=null||w.Stage=="等待曲面稳定…",stage=w?.Stage??"等待检查",error=w?.Error};
    }
    internal static IEnumerable<(RhinoObject Object,PlantBillboard Billboard,bool Manual,string Path)> Drawables(RhinoDoc doc,RhinoObject obj)
    {
        var cache=Decoded(obj);var spec=cache.Spec;double units=RhinoMath.UnitScale(doc.ModelUnitSystem,UnitSystem.Meters);var images=spec.Assets.ToDictionary(p=>p.Key,p=>PlantService.Image(p.Value.Image,p.Value.Sha256));var matrix=Matrix(obj);var xs=new Vector3d(1,0,0);xs.Transform(matrix);var ys=new Vector3d(0,1,0);ys.Transform(matrix);var zs=new Vector3d(0,0,1);zs.Transform(matrix);double widthScale=Math.Sqrt(xs.Length*ys.Length),heightScale=zs.Length;
        foreach(var row in cache.Rows)
        {
            if(!spec.Assets.TryGetValue(row.Asset,out var a))continue;var p=row.Position/units;
            var billboard=new PlantBillboard(obj.Id+"/"+row.Id,a.ScientificName,a.ScientificName+(row.Manual?" · 手工":" · 自动"),p,a.WidthMeters*row.Scale/units*widthScale,a.HeightMeters*row.Scale/units*heightScale,a.AnchorU,a.AnchorV,row.Mirror,images[row.Asset]);
            yield return(obj,billboard with{AssetId=a.Asset},row.Manual,a.Image);
        }
    }
}
