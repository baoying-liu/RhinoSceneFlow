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
    public double WidthMeters { get; set; } = 1;
    public double HeightMeters { get; set; } = 1;
    public double Roughness { get; set; } = .65;
    public double Metallic { get; set; }
    public string RecommendedMapping { get; set; } = "auto";
    public string Source { get; set; } = "import";
    public string Prompt { get; set; } = "";
    public DateTime CreatedUtc { get; set; } = DateTime.UtcNow;
    public Dictionary<string,string> Maps { get; set; } = [];
    public Dictionary<string,string> Sha256 { get; set; } = [];
    public void Validate()
    {
        Category??="";Tags??=[];
        if(SchemaVersion!=1||Id==Guid.Empty||Revision<1||string.IsNullOrWhiteSpace(Name)||Name.Length>200)throw new ArgumentException("Invalid material identity/name.");
        if(!double.IsFinite(WidthMeters)||!double.IsFinite(HeightMeters)||WidthMeters<=0||HeightMeters<=0||WidthMeters>1e5||HeightMeters>1e5)throw new ArgumentException("Texture physical size must be finite and positive (meters).");
        if(!double.IsFinite(Roughness)||!double.IsFinite(Metallic)||Roughness<0||Roughness>1||Metallic<0||Metallic>1)throw new ArgumentException("Roughness/metallic must be in 0..1.");
        if(RecommendedMapping is not ("auto" or "plane" or "box" or "cylinder"))throw new ArgumentException("Unknown mapping mode.");
        if(Maps is null||Sha256 is null||!Maps.ContainsKey("baseColor")||Maps.Keys.Any(k=>!MaterialLibrary.Slots.Contains(k)))throw new ArgumentException("A baseColor map is required; supported maps: baseColor, roughness, normal, metallic.");
        if(Maps.Values.Any(v=>string.IsNullOrWhiteSpace(v)||Path.IsPathRooted(v)||v.Contains(':')||v.Split('/','\\').Any(p=>p is ".." or ".")))throw new ArgumentException("Material map paths must stay relative to the asset.");
    }
}

/// <summary>Portable immutable image files with relative references and atomic metadata updates.</summary>
public sealed class MaterialLibrary
{
    public static readonly string[] Slots=["baseColor","roughness","normal","metallic"];
    public static readonly JsonSerializerOptions Json=new(){PropertyNamingPolicy=JsonNamingPolicy.CamelCase,PropertyNameCaseInsensitive=true,WriteIndented=true};
    public string Root { get; }
    public MaterialLibrary(string root){if(!Path.IsPathFullyQualified(root))throw new ArgumentException("Library path must be absolute.");Root=Path.GetFullPath(root);}
    public static T Clone<T>(T value)=>JsonSerializer.Deserialize<T>(JsonSerializer.Serialize(value,Json),Json)!;
    public string AssetDirectory(Guid id)=>Path.Combine(Root,"assets",id.ToString("N"));
    public MaterialAsset[] List(string query="")
    {
        string directory=Path.Combine(Root,"assets");if(!Directory.Exists(directory))return [];
        return Directory.EnumerateDirectories(directory).Where(d=>Guid.TryParseExact(Path.GetFileName(d),"N",out _)&&File.Exists(Path.Combine(d,"asset.json")))
            .Select(d=>Read(Path.Combine(d,"asset.json"))).Where(a=>string.IsNullOrWhiteSpace(query)||
                (a.Name+" "+a.Category+" "+string.Join(" ",a.Tags)).Contains(query,StringComparison.OrdinalIgnoreCase)).OrderBy(a=>a.Name).ToArray();
    }
    private static MaterialAsset Read(string path){var a=JsonSerializer.Deserialize<MaterialAsset>(File.ReadAllText(path),Json)??throw new InvalidDataException("Empty asset metadata.");a.Validate();return a;}
    public MaterialAsset Get(Guid id){var a=Read(Path.Combine(AssetDirectory(id),"asset.json"));if(a.Id!=id)throw new InvalidDataException("Material identity mismatch.");return a;}
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
        if(!files.ContainsKey("baseColor")||files.Keys.Any(k=>!Slots.Contains(k)))throw new ArgumentException("Select baseColor and supported optional maps.");
        var a=Clone(descriptor);a.Id=Guid.NewGuid();a.Revision=1;a.CatalogRevision=1;a.CreatedUtc=DateTime.UtcNow;a.Maps=[];a.Sha256=[];
        foreach(var (slot,path) in files)
        {if(!Path.IsPathFullyQualified(path)||!File.Exists(path))throw new FileNotFoundException("Image not found.",path);string ext=Path.GetExtension(path).ToLowerInvariant();if(ext is not (".png" or ".jpg" or ".jpeg"))throw new ArgumentException("Use PNG or JPEG images.");if(new FileInfo(path).Length>256L*1024*1024)throw new ArgumentException("Individual map limit: 256 MiB.");a.Maps[slot]=a.Id.ToString("N")+"_"+slot+ext;}
        a.Validate();Directory.CreateDirectory(Path.Combine(Root,"assets"));string target=AssetDirectory(a.Id),staging=target+".staging";Directory.CreateDirectory(staging);
        try
        {
            foreach(var (slot,path) in files){string dest=Path.Combine(staging,a.Maps[slot]);File.Copy(path,dest);a.Sha256[slot]=Hash(dest);}
            File.WriteAllText(Path.Combine(staging,"asset.json"),JsonSerializer.Serialize(a,Json));Directory.Move(staging,target);return a;
        }
        finally{if(Directory.Exists(staging))Directory.Delete(staging,true);}
    }
    public MaterialAsset Update(MaterialAsset descriptor)
    {
        var old=Get(descriptor.Id);var a=Clone(descriptor);a.Maps=old.Maps;a.Sha256=old.Sha256;a.Source=old.Source;a.Prompt=old.Prompt;a.CreatedUtc=old.CreatedUtc;a.Revision=old.Revision+1;a.CatalogRevision=old.CatalogRevision+1;a.Validate();Verify(a);
        string path=Path.Combine(AssetDirectory(a.Id),"asset.json"),temp=path+".tmp";File.WriteAllText(temp,JsonSerializer.Serialize(a,Json));File.Move(temp,path,true);return a;
    }
    public MaterialAsset UpdateLabels(Guid id,string name,string category,string[] tags)
    {
        var a=Get(id);var label=MaterialCatalog.ValidatePlan([a],[new(id,name,category,tags)]).Single();
        a.Name=label.Name;a.Category=label.Category;a.Tags=label.Tags;a.CatalogRevision++;a.Validate();
        string path=Path.Combine(AssetDirectory(id),"asset.json");File.WriteAllText(path+".tmp",JsonSerializer.Serialize(a,Json));File.Move(path+".tmp",path,true);return a;
    }
    public void ExportPackage(Guid id,string path)
    {
        var a=Get(id);Verify(a);if(!Path.IsPathFullyQualified(path)||!path.EndsWith(".zip",StringComparison.OrdinalIgnoreCase)||File.Exists(path))throw new ArgumentException("Choose a new absolute ZIP path.");
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);string temp=path+"."+Guid.NewGuid().ToString("N")+".tmp";
        try{using(var zip=ZipFile.Open(temp,ZipArchiveMode.Create)){zip.CreateEntryFromFile(Path.Combine(AssetDirectory(id),"asset.json"),"asset.json");foreach(var map in a.Maps.Values)zip.CreateEntryFromFile(Path.Combine(AssetDirectory(id),map),map);}File.Move(temp,path);}
        finally{if(File.Exists(temp))File.Delete(temp);}
    }
    public MaterialAsset ImportPackage(string path,Action<IReadOnlyDictionary<string,string>>? validate=null)
    {
        string temp=Directory.CreateTempSubdirectory("SceneFlow-material-").FullName;
        try
        {
            using var zip=ZipFile.OpenRead(path);if(zip.Entries.Count>6||zip.Entries.Sum(e=>e.Length)>1024L*1024*1024)throw new InvalidDataException("Invalid/oversized material package.");
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
