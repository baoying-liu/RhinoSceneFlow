using System.Security.Cryptography;
using System.Text.Json;
using System.IO.Compression;

namespace RhinoSceneFlow.Core;

public sealed class MaterialAsset
{
    public int SchemaVersion { get; set; } = 1;
    public Guid Id { get; set; } = Guid.NewGuid();
    public int Revision { get; set; } = 1;
    public int CatalogRevision { get; set; } = 1;
    public string Name { get; set; } = "Material";
    public string Category { get; set; } = "";
    public string[] Tags { get; set; } = [];
    public Dictionary<string,AssetLocaleText> Localizations {get;set;}=[];
    public double WidthMeters { get; set; } = 1;
    public double HeightMeters { get; set; } = 1;
    public double Roughness { get; set; } = .65;
    public double Metallic { get; set; }
    public string RecommendedMapping { get; set; } = "auto";
    public string Source { get; set; } = "import";
    public string Prompt { get; set; } = "";
    public TextureRandomization Randomization { get; set; } = new();
    public PlantIdentity? Plant { get; set; }
    public SeasonalAppearance Seasonal {get;set;}=new();
    public DateTime CreatedUtc { get; set; } = DateTime.UtcNow;
    public Dictionary<string,string> Maps { get; set; } = [];
    public Dictionary<string,string> Sha256 { get; set; } = [];
    public void Validate()
    {
        Category??="";Tags??=[];Localizations??=[];AssetLocalization.Validate(this);
        Randomization??=new();Randomization.Validate();
        Plant?.Validate();
        if(SchemaVersion!=1||Id==Guid.Empty||Revision<1||string.IsNullOrWhiteSpace(Name)||Name.Length>200)throw new ArgumentException("Invalid material identity/name.");
        if(!double.IsFinite(WidthMeters)||!double.IsFinite(HeightMeters)||WidthMeters<=0||HeightMeters<=0||WidthMeters>1e5||HeightMeters>1e5)throw new ArgumentException("Texture physical size must be finite and positive (meters).");
        if(!double.IsFinite(Roughness)||!double.IsFinite(Metallic)||Roughness<0||Roughness>1||Metallic<0||Metallic>1)throw new ArgumentException("Roughness/metallic must be in 0..1.");
        if(RecommendedMapping is not ("auto" or "plane" or "box" or "cylinder"))throw new ArgumentException("Unknown mapping mode.");
        if(Maps is null||Sha256 is null||!Maps.ContainsKey("baseColor")||Maps.Keys.Any(k=>!MaterialLibrary.ValidSlot(k)))throw new ArgumentException("A baseColor and supported map slots are required.");
        Seasonal??=new();Seasonal.Validate(this);
        if(Maps.Values.Any(v=>string.IsNullOrWhiteSpace(v)||Path.IsPathRooted(v)||v.Contains(':')||v.Split('/','\\').Any(p=>p is ".." or ".")))throw new ArgumentException("Material map paths must stay relative to the asset.");
    }
}

/// <summary>Portable immutable image files with relative references and atomic metadata updates.</summary>
public sealed class MaterialLibrary
{
    public static readonly string[] Slots=["baseColor","roughness","normal","metallic"];
    public static bool ValidSlot(string slot)=>Slots.Contains(slot)||Seasons.All.Any(s=>slot==s+"_elevation"||slot==s+"_plan");
    public static readonly JsonSerializerOptions Json=new(){PropertyNamingPolicy=JsonNamingPolicy.CamelCase,PropertyNameCaseInsensitive=true,WriteIndented=true};
    public string Root { get; }
    public MaterialLibrary(string root){if(!Path.IsPathFullyQualified(root))throw new ArgumentException("Library path must be absolute.");Root=Path.TrimEndingDirectorySeparator(Path.GetFullPath(root));}
    internal T Locked<T>(Func<T> action){using var lease=LibraryFileLock.Enter(Root);Recover();return action();}
    private string Journal=>Path.Combine(Root,".sceneflow-catalog-rollback.json");
    private static void RetryCommit(Action commit)
    {
        var clock=System.Diagnostics.Stopwatch.StartNew();
        while(true){try{commit();return;}catch(Exception e) when((e is IOException or UnauthorizedAccessException)&&clock.Elapsed<TimeSpan.FromSeconds(1)){Thread.Sleep(20);}}
    }
    internal static void AtomicWrite(string path,string text)
    {
        string temp=path+"."+Guid.NewGuid().ToString("N")+".tmp";
        try
        {
            using(var file=new FileStream(temp,FileMode.CreateNew,FileAccess.Write,FileShare.None)){byte[] data=System.Text.Encoding.UTF8.GetBytes(text);file.Write(data);file.Flush(true);}
            RetryCommit(()=>File.Move(temp,path,true));
        }
        finally{if(File.Exists(temp))File.Delete(temp);}
    }
    private void Recover()
    {
        if(!File.Exists(Journal))return;
        var backups=JsonSerializer.Deserialize<Dictionary<Guid,string>>(File.ReadAllText(Journal),Json)??throw new InvalidDataException("Invalid catalog recovery journal.");
        foreach(var (id,text) in backups){var asset=JsonSerializer.Deserialize<MaterialAsset>(text,Json)??throw new InvalidDataException("Invalid recovery asset.");asset.Validate();if(asset.Id!=id)throw new InvalidDataException("Recovery identity mismatch.");}
        foreach(var (id,text) in backups)AtomicWrite(Path.Combine(AssetDirectory(id),"asset.json"),text);
        File.Delete(Journal);
    }
    // Caller holds the library lease through validation, journal, commit or rollback.
    internal void CommitCatalog(MaterialAsset[] assets)
    {
        var backups=assets.ToDictionary(a=>a.Id,a=>File.ReadAllText(Path.Combine(AssetDirectory(a.Id),"asset.json")));
        AtomicWrite(Journal,JsonSerializer.Serialize(backups,Json));
        try{foreach(var a in assets)AtomicWrite(Path.Combine(AssetDirectory(a.Id),"asset.json"),JsonSerializer.Serialize(a,Json));File.Delete(Journal);}
        catch{Recover();throw;}
    }
    public static T Clone<T>(T value)=>JsonSerializer.Deserialize<T>(JsonSerializer.Serialize(value,Json),Json)!;
    public string AssetDirectory(Guid id)=>Path.Combine(Root,"assets",id.ToString("N"));
    public MaterialAsset[] List(string query="")=>Locked(()=>
    {
        string directory=Path.Combine(Root,"assets");if(!Directory.Exists(directory))return [];
        return Directory.EnumerateDirectories(directory).Where(d=>Guid.TryParseExact(Path.GetFileName(d),"N",out _)&&File.Exists(Path.Combine(d,"asset.json")))
            .Select(d=>Read(Path.Combine(d,"asset.json"))).Where(a=>string.IsNullOrWhiteSpace(query)||
                (a.Name+" "+a.Category+" "+string.Join(" ",a.Tags)).Contains(query,StringComparison.OrdinalIgnoreCase)).OrderBy(a=>a.Name).ToArray();
    });
    private static MaterialAsset Read(string path){var a=JsonSerializer.Deserialize<MaterialAsset>(File.ReadAllText(path),Json)??throw new InvalidDataException("Empty asset metadata.");a.Validate();return a;}
    public MaterialAsset Get(Guid id)=>Locked(()=>{var a=Read(Path.Combine(AssetDirectory(id),"asset.json"));if(a.Id!=id)throw new InvalidDataException("Material identity mismatch.");return a;});
    public string MapPath(MaterialAsset asset,string slot)
    {
        asset.Validate();string directory=Path.GetFullPath(AssetDirectory(asset.Id))+Path.DirectorySeparatorChar;
        string path=Path.GetFullPath(Path.Combine(directory,asset.Maps[slot]));
        if(!path.StartsWith(directory,StringComparison.OrdinalIgnoreCase)||!File.Exists(path))throw new InvalidDataException("Missing/outside material image: "+slot);
        return path;
    }
    public void Verify(MaterialAsset asset)
    {
        foreach(var slot in asset.Maps.Keys)
        {string path=MapPath(asset,slot);if(!asset.Sha256.TryGetValue(slot,out var hash)||!Hash(path).Equals(hash,StringComparison.OrdinalIgnoreCase))throw new InvalidDataException("Material image checksum mismatch: "+slot);}
    }
    public MaterialAsset Import(MaterialAsset descriptor,IReadOnlyDictionary<string,string> files)
    {
        if(!files.ContainsKey("baseColor")||files.Keys.Any(k=>!ValidSlot(k)))throw new ArgumentException("Select baseColor and supported optional maps.");
        var a=Clone(descriptor);a.Id=Guid.NewGuid();a.Revision=1;a.CatalogRevision=1;a.CreatedUtc=DateTime.UtcNow;a.Maps=[];a.Sha256=[];
        foreach(var (slot,path) in files)
        {if(!Path.IsPathFullyQualified(path)||!File.Exists(path))throw new FileNotFoundException("Image not found.",path);string ext=Path.GetExtension(path).ToLowerInvariant();if(ext is not (".png" or ".jpg" or ".jpeg"))throw new ArgumentException("Use PNG or JPEG images.");if(new FileInfo(path).Length>256L*1024*1024)throw new ArgumentException("Individual map limit: 256 MiB.");a.Maps[slot]=a.Id.ToString("N")+"_"+slot+ext;}
        if(!a.Seasonal.Variants.ContainsKey("summer"))a.Seasonal.Variants["summer"]=new(){Elevation="baseColor",CrownWidthMeters=a.WidthMeters};
        a.Validate();Directory.CreateDirectory(Path.Combine(Root,"assets"));string target=AssetDirectory(a.Id),staging=target+".staging";Directory.CreateDirectory(staging);
        try
        {
            foreach(var (slot,path) in files){string dest=Path.Combine(staging,a.Maps[slot]);File.Copy(path,dest);a.Sha256[slot]=Hash(dest);}
            AtomicWrite(Path.Combine(staging,"asset.json"),JsonSerializer.Serialize(a,Json));return Locked(()=>{RetryCommit(()=>Directory.Move(staging,target));return a;});
        }
        finally{if(Directory.Exists(staging))Directory.Delete(staging,true);}
    }
    public MaterialAsset Update(MaterialAsset descriptor)=>Locked(()=>
    {
        var old=Get(descriptor.Id);if(descriptor.Revision!=old.Revision||descriptor.CatalogRevision!=old.CatalogRevision)throw new InvalidOperationException("材质已被其他操作更新，请刷新并重新选择后再保存。");
        var a=Clone(descriptor);a.Maps=old.Maps;a.Sha256=old.Sha256;a.Source=old.Source;a.Prompt=old.Prompt;a.CreatedUtc=old.CreatedUtc;a.Revision=old.Revision+1;a.CatalogRevision=old.CatalogRevision+1;a.Validate();Verify(a);
        AtomicWrite(Path.Combine(AssetDirectory(a.Id),"asset.json"),JsonSerializer.Serialize(a,Json));return a;
    });
    public MaterialAsset AddSeason(Guid id,int revision,string season,bool plan,string? imagePath,string? reuseSlot=null,double crownWidthMeters=3,double? elevationWidthMeters=null,double? anchorU=null)=>Locked(()=>
    {
        Seasons.Validate(season);var a=Get(id);if(a.Revision!=revision)throw new InvalidOperationException("素材已变化，请刷新后重试。");
        string slot=reuseSlot??season+(plan?"_plan":"_elevation");string? copied=null;
        try
        {
            if(imagePath!=null)
            {
                if(!Path.IsPathFullyQualified(imagePath)||!File.Exists(imagePath)||new FileInfo(imagePath).Length>256L*1024*1024)throw new ArgumentException("Invalid seasonal image.");
                string ext=Path.GetExtension(imagePath).ToLowerInvariant();if(ext is not (".png" or ".jpg" or ".jpeg"))throw new ArgumentException("Seasonal image must be PNG/JPEG.");
                string name=Guid.NewGuid().ToString("N")+"_"+slot+ext;copied=Path.Combine(AssetDirectory(id),name);File.Copy(imagePath,copied);a.Maps[slot]=name;a.Sha256[slot]=Hash(copied);
            }
            else if(!a.Maps.ContainsKey(slot))throw new ArgumentException("Reusable seasonal slot is missing.");
            if(!a.Seasonal.Variants.TryGetValue(season,out var variant))a.Seasonal.Variants[season]=variant=new();
            if(plan){variant.Plan=slot;variant.CrownWidthMeters=crownWidthMeters;}else
            {
                var geometry=a.Seasonal.Variants.Values.FirstOrDefault(v=>v.Elevation==slot&&v.ElevationWidthMeters.HasValue);
                variant.Elevation=slot;variant.ElevationWidthMeters=elevationWidthMeters??geometry?.ElevationWidthMeters;variant.AnchorU=anchorU??geometry?.AnchorU;
            }
            a.Revision++;a.Validate();Verify(a);AtomicWrite(Path.Combine(AssetDirectory(id),"asset.json"),JsonSerializer.Serialize(a,Json));return a;
        }
        catch{if(copied!=null&&File.Exists(copied))File.Delete(copied);throw;}
    });
    public MaterialAsset UpdateLabels(Guid id,string name,string category,string[] tags,int? expectedCatalogRevision=null)=>Locked(()=>
    {
        var a=Get(id);if(expectedCatalogRevision.HasValue&&a.CatalogRevision!=expectedCatalogRevision)throw new InvalidOperationException("材质属性已更新，请刷新并重新选择后再保存。");var label=MaterialCatalog.ValidatePlan([a],[new(id,name,category,tags)]).Single();
        a.Name=label.Name;a.Category=label.Category;a.Tags=label.Tags;a.CatalogRevision++;a.Validate();
        AtomicWrite(Path.Combine(AssetDirectory(id),"asset.json"),JsonSerializer.Serialize(a,Json));return a;
    });
    public void ExportPackage(Guid id,string path)
    {
        var a=Get(id);Verify(a);if(!Path.IsPathFullyQualified(path)||!path.EndsWith(".zip",StringComparison.OrdinalIgnoreCase)||File.Exists(path))throw new ArgumentException("Choose a new absolute ZIP path.");
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);string temp=path+"."+Guid.NewGuid().ToString("N")+".tmp";
        try{using(var zip=ZipFile.Open(temp,ZipArchiveMode.Create)){using(var writer=new StreamWriter(zip.CreateEntry("asset.json").Open()))writer.Write(JsonSerializer.Serialize(a,Json));foreach(var map in a.Maps.Values)zip.CreateEntryFromFile(Path.Combine(AssetDirectory(id),map),map);}File.Move(temp,path);}
        finally{if(File.Exists(temp))File.Delete(temp);}
    }
    public MaterialAsset ImportPackage(string path,Action<IReadOnlyDictionary<string,string>>? validate=null)
    {
        string temp=Directory.CreateTempSubdirectory("SceneFlow-material-").FullName;
        try
        {
            using var zip=ZipFile.OpenRead(path);if(zip.Entries.Count>16||zip.Entries.Sum(e=>e.Length)>1024L*1024*1024)throw new InvalidDataException("Invalid/oversized material package.");
            var names=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach(var entry in zip.Entries)
            {if(entry.Name!=entry.FullName||entry.FullName.Contains('\\')||entry.FullName.Contains(':')||!names.Add(entry.FullName))throw new InvalidDataException("Invalid package path.");entry.ExtractToFile(Path.Combine(temp,entry.Name));}
            var a=Read(Path.Combine(temp,"asset.json"));var files=a.Maps.ToDictionary(v=>v.Key,v=>Path.Combine(temp,v.Value));
            foreach(var (slot,file) in files)if(!a.Sha256.TryGetValue(slot,out var hash)||Hash(file)!=hash)throw new InvalidDataException("Package checksum mismatch.");
            validate?.Invoke(files);
            return Import(a,files);
        }
        finally{Directory.Delete(temp,true);}
    }
    private static string Hash(string path){using var s=File.OpenRead(path);return Convert.ToHexString(SHA256.HashData(s));}
}
