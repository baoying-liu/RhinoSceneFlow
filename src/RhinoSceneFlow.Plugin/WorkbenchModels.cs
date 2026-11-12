using Rhino;
using Rhino.Display;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class ExportLayerSetting
{
    public string Kind{get;set;}=""; // empty placeholder, shadow, material (legacy color), texture, display
    public string TextureGrouping{get;set;}="material";
    public string PlantGrouping{get;set;}="species";
    public string ColorSource{get;set;}="material";
    public Guid Mode{get;set;}
    public string Blend{get;set;}="norm";
    public int Opacity{get;set;}=100;
    public bool Enabled{get;set;}=true;
    public bool Visible{get;set;}=true;
    public bool Expanded{get;set;}
    public ExportLayerSetting Copy()=>new(){Kind=Kind,TextureGrouping=TextureGrouping,PlantGrouping=PlantGrouping,ColorSource=ColorSource,Mode=Mode,Blend=Blend,Opacity=Opacity,Enabled=Enabled,Visible=Visible,Expanded=Expanded};
}
public sealed class CameraAdjustment
{
    public double Yaw{get;set;}
    public double Pitch{get;set;}
    public double Zoom{get;set;}=1;
    public double PanX{get;set;}
    public double PanY{get;set;}
    public double PanZ{get;set;}
}
public sealed class SunAdjustment
{
    public bool UseDocument{get;set;}=true;
    public double Azimuth{get;set;}=135;
    public double Altitude{get;set;}=45;
}
public sealed class ViewExportRow
{
    public Guid Id{get;set;}
    public string Name{get;set;}="";
    public bool Included{get;set;}=true;
    public int Width{get;set;}=2048;
    public int Height{get;set;}=1280;
    public Guid Mode{get;set;}=DisplayModeDescription.RenderedId;
    public string PreviewSeason{get;set;}="summer";
    public bool FollowPreviewSeason{get;set;}=true;
    public string[] ExportSeasons{get;set;}=["summer"];
    public bool SeasonExpanded{get;set;}
    public string Status{get;set;}="待导出";
    public static List<ExportLayerSetting> DefaultLayers()=>[new(){Kind="plants"},new(){Kind="shadow",Blend="mul "},new(){Kind="texture"},new(){Kind="display",Mode=WorkbenchService.Modes().FirstOrDefault(m=>m.EnglishName=="Arctic")?.Id??Guid.Empty},new(){Kind="depth",Visible=false},new(){Kind="color",Visible=false}];
    public List<ExportLayerSetting> Layers{get;set;}=DefaultLayers();
    public int LayerDefaultsVersion{get;set;}
    public bool SizeExpanded{get;set;}
    public bool LayerSettingsExpanded{get;set;}
    public bool PlantsInitialized{get;set;}
    public bool PlantShadows{get;set;}=true;
    public bool SeparatePlantShadows{get;set;}=true;
    public CameraAdjustment Camera{get;set;}=new();
    public SunAdjustment Sun{get;set;}=new();
    public ViewExportRow Copy()=>WorkbenchStore.Clone(this);
    internal void InitializePlants()
    {
        if(!PlantsInitialized){if(!Layers.Any(l=>l.Kind=="plants"))Layers.Insert(0,new(){Kind="plants"});PlantsInitialized=true;}
        // Only upgrade the untouched historical default. Explicit custom stacks stay intact.
        if(LayerDefaultsVersion==0&&Layers.Count==3&&Layers.Select(l=>l.Kind).SequenceEqual(new[]{"plants","shadow","texture"})&&Layers.All(l=>l.Enabled&&l.Visible&&l.Opacity==100&&l.TextureGrouping=="material"&&l.PlantGrouping=="species"&&l.Blend==(l.Kind=="shadow"?"mul ":"norm")))Layers.AddRange(DefaultLayers().Skip(3));
        LayerDefaultsVersion=1;
    }
    public void SetPreset(int longest)
    {
        if(longest is not (1024 or 2048 or 4096 or 8192))throw new ArgumentException("请选择 1K / 2K / 4K / 8K。");
        double ratio=(double)Width/Height;
        if(ratio>=1){Width=longest;Height=Math.Max(64,(int)Math.Round(longest/ratio));}
        else{Height=longest;Width=Math.Max(64,(int)Math.Round(longest*ratio));}
    }
    public void Validate()
    {
        Seasons.Validate(PreviewSeason);if(ExportSeasons==null||ExportSeasons.Length==0||ExportSeasons.Distinct().Count()!=ExportSeasons.Length)throw new ArgumentException("请选择不重复的导出季节。");foreach(string s in ExportSeasons)Seasons.Validate(s);
        if(Layers is null||Camera is null||Sun is null||Layers.Any(l=>l is null))throw new ArgumentException("图层、相机和太阳配置不能为空。");
        if(Width<64||Height<64||Width>8192||Height>8192)throw new ArgumentException("宽高需为 64–8192 像素。");
        if(!WorkbenchService.Modes().Any(m=>m.Id==Mode))throw new ArgumentException($"{Name} 的预览显示模式不存在。");
        if(Layers.Count>32)throw new ArgumentException("每个视图最多设置 32 个通道/显示模式。");
        var active=Layers.Where(l=>l.Enabled).ToArray();
        if(active.Length==0||active.Any(l=>l.Kind is not ("shadow" or "material" or "texture" or "display" or "plants" or "color" or "depth")))throw new ArgumentException($"{Name}：请选择每个启用图层的内容，或关闭空条目。");
        foreach(var l in active)
            if(l.Kind=="plants"&&l.PlantGrouping is not ("individual" or "species" or "all"))throw new ArgumentException("植物分层：单株、按学名或合并全部。");
            else
            if(l.Kind is "texture" or "color"&&l.TextureGrouping is not ("material" or "object" or "all"))throw new ArgumentException("请选择按材质、按物件或全部合并。");
            else if(l.Kind=="color"&&l.ColorSource is not ("material" or "layer"))throw new ArgumentException("颜色来源：material | layer。");
            else if(!ConfiguredStack.BlendKeys.Contains(l.Blend)||l.Opacity<0||l.Opacity>100||l.Kind=="display"&&!WorkbenchService.Modes().Any(m=>m.Id==l.Mode))throw new ArgumentException($"{Name}：图层模式或透明度无效。");
        double[] numbers=[Camera.Yaw,Camera.Pitch,Camera.Zoom,Camera.PanX,Camera.PanY,Camera.PanZ,Sun.Azimuth,Sun.Altitude];
        if(numbers.Any(v=>!double.IsFinite(v))||Math.Abs(Camera.Yaw)>180||Camera.Zoom<.01||Camera.Zoom>100||Math.Abs(Camera.Pitch)>89||Sun.Azimuth<0||Sun.Azimuth>360||Sun.Altitude<.1||Sun.Altitude>90)throw new ArgumentException("相机/太阳设置超出有效范围。");
    }
}

internal static class WorkbenchStore
{
    internal static readonly JsonSerializerOptions Json=new(){PropertyNamingPolicy=JsonNamingPolicy.CamelCase,PropertyNameCaseInsensitive=true,WriteIndented=true};
    private static readonly Dictionary<uint,ViewExportRow[]> session=[];
    static WorkbenchStore()
    {
        RhinoDoc.CloseDocument+=(_,e)=>session.Remove(e.Document.RuntimeSerialNumber);
        RhinoDoc.EndSaveDocument+=(_,e)=>
        {
            if(e.ExportSelected||string.IsNullOrWhiteSpace(e.FileName)||!e.FileName.EndsWith(".3dm",StringComparison.OrdinalIgnoreCase)||!session.TryGetValue(e.Document.RuntimeSerialNumber,out var rows))return;
            try{Write(PathForKey(System.IO.Path.GetFullPath(e.FileName).ToUpperInvariant()),rows);}
            catch(Exception error){System.Diagnostics.Debug.WriteLine("SceneFlow settings save: "+error.Message);}
        };
    }
    internal static T Clone<T>(T value)=>JsonSerializer.Deserialize<T>(JsonSerializer.Serialize(value,Json),Json)!;
    private static string PathFor(RhinoDoc doc)
    {
        string key=string.IsNullOrWhiteSpace(doc.Path)?"unsaved-"+Environment.ProcessId+"-"+doc.RuntimeSerialNumber:System.IO.Path.GetFullPath(doc.Path).ToUpperInvariant();
        return PathForKey(key);
    }
    private static string PathForKey(string key)=>System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"RhinoSceneFlow","workbench",Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(key)))+".json");
    internal static ViewExportRow[] Load(RhinoDoc doc)
    {
        if(session.TryGetValue(doc.RuntimeSerialNumber,out var cached))return Clone(cached);
        string path=PathFor(doc);var rows=File.Exists(path)?JsonSerializer.Deserialize<ViewExportRow[]>(File.ReadAllText(path),Json)??[]:[];
        session[doc.RuntimeSerialNumber]=Clone(rows);return rows;
    }
    internal static void Save(RhinoDoc doc,IEnumerable<ViewExportRow> rows)
    {
        var snapshot=Clone(rows.ToArray());Write(PathFor(doc),snapshot);session[doc.RuntimeSerialNumber]=snapshot;
    }
    private static void Write(string path,ViewExportRow[] rows)
    {
        Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path)!);
        string temporary=path+"."+Guid.NewGuid().ToString("N")+".tmp";
        try{File.WriteAllText(temporary,JsonSerializer.Serialize(rows,Json));File.Move(temporary,path,true);}
        finally{if(File.Exists(temporary))File.Delete(temporary);}
    }
}
