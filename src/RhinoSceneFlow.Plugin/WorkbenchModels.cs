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
    public Guid Mode{get;set;}
    public string Blend{get;set;}="norm";
    public int Opacity{get;set;}=100;
    public bool Enabled{get;set;}=true;
    public ExportLayerSetting Copy()=>new(){Kind=Kind,TextureGrouping=TextureGrouping,PlantGrouping=PlantGrouping,Mode=Mode,Blend=Blend,Opacity=Opacity,Enabled=Enabled};
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
    public Guid Mode{get;set;}=DisplayModeDescription.ShadedId;
    public string Status{get;set;}="待导出";
    public List<ExportLayerSetting> Layers{get;set;}=[new(){Kind="plants"},new(){Kind="shadow",Blend="mul "},new(){Kind="texture"}];
    public bool PlantsInitialized{get;set;}
    public bool PlantShadows{get;set;}=true;
    public CameraAdjustment Camera{get;set;}=new();
    public SunAdjustment Sun{get;set;}=new();
    public ViewExportRow Copy()=>WorkbenchStore.Clone(this);
    internal void InitializePlants(){if(PlantsInitialized)return;if(!Layers.Any(l=>l.Kind=="plants"))Layers.Insert(0,new(){Kind="plants"});PlantsInitialized=true;}
    public void SetPreset(int longest)
    {
        if(longest is not (1024 or 2048 or 4096 or 8192))throw new ArgumentException("请选择 1K / 2K / 4K / 8K。");
        double ratio=(double)Width/Height;
        if(ratio>=1){Width=longest;Height=Math.Max(64,(int)Math.Round(longest/ratio));}
        else{Height=longest;Width=Math.Max(64,(int)Math.Round(longest*ratio));}
    }
    public void Validate()
    {
        if(Layers is null||Camera is null||Sun is null||Layers.Any(l=>l is null))throw new ArgumentException("图层、相机和太阳配置不能为空。");
        if(Width<64||Height<64||Width>8192||Height>8192)throw new ArgumentException("宽高需为 64–8192 像素。");
        if(!WorkbenchService.Modes().Any(m=>m.Id==Mode))throw new ArgumentException($"{Name} 的预览显示模式不存在。");
        if(Layers.Count>32)throw new ArgumentException("每个视图最多设置 32 个通道/显示模式。");
        var active=Layers.Where(l=>l.Enabled).ToArray();
        if(active.Length==0||active.Any(l=>l.Kind is not ("shadow" or "material" or "texture" or "display" or "plants")))throw new ArgumentException($"{Name}：请选择每个启用图层的内容，或关闭空条目。");
        foreach(var l in active)
            if(l.Kind=="plants"&&l.PlantGrouping is not ("individual" or "species" or "all"))throw new ArgumentException("植物分层：单株、按学名或合并全部。");
            else
            if(l.Kind=="texture"&&l.TextureGrouping is not ("material" or "object"))throw new ArgumentException("材质贴图请选择按材质或按物件分层。");
            else if(!ConfiguredStack.BlendKeys.Contains(l.Blend)||l.Opacity<0||l.Opacity>100||l.Kind=="display"&&!WorkbenchService.Modes().Any(m=>m.Id==l.Mode))throw new ArgumentException($"{Name}：图层模式或透明度无效。");
        double[] numbers=[Camera.Yaw,Camera.Pitch,Camera.Zoom,Camera.PanX,Camera.PanY,Camera.PanZ,Sun.Azimuth,Sun.Altitude];
        if(numbers.Any(v=>!double.IsFinite(v))||Math.Abs(Camera.Yaw)>180||Camera.Zoom<.01||Camera.Zoom>100||Math.Abs(Camera.Pitch)>89||Sun.Azimuth<0||Sun.Azimuth>360||Sun.Altitude<.1||Sun.Altitude>90)throw new ArgumentException("相机/太阳设置超出有效范围。");
    }
}

internal static class WorkbenchStore
{
    internal static readonly JsonSerializerOptions Json=new(){PropertyNamingPolicy=JsonNamingPolicy.CamelCase,PropertyNameCaseInsensitive=true,WriteIndented=true};
    internal static T Clone<T>(T value)=>JsonSerializer.Deserialize<T>(JsonSerializer.Serialize(value,Json),Json)!;
    private static string PathFor(RhinoDoc doc)
    {
        string key=string.IsNullOrWhiteSpace(doc.Path)?"unsaved-"+Environment.ProcessId+"-"+doc.RuntimeSerialNumber:System.IO.Path.GetFullPath(doc.Path).ToUpperInvariant();
        return System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"RhinoSceneFlow","workbench",Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(key)))+".json");
    }
    internal static ViewExportRow[] Load(RhinoDoc doc)
    {
        string path=PathFor(doc);if(!File.Exists(path))return [];
        return JsonSerializer.Deserialize<ViewExportRow[]>(File.ReadAllText(path),Json)??[];
    }
    internal static void Save(RhinoDoc doc,IEnumerable<ViewExportRow> rows)
    {
        string path=PathFor(doc);Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path)!);
        string temporary=path+".tmp";File.WriteAllText(temporary,JsonSerializer.Serialize(rows,Json));File.Move(temporary,path,true);
    }
}
