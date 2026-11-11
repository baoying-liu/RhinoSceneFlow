using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
namespace RhinoSceneFlow.Core;

/// <summary>Structured AI labels. Tags retain the exact order of canonical Tags.</summary>
public sealed record AssetLocaleLabel(string Language,string Name,string Category,string[] Tags,string Reason);
public sealed class AssetLocaleText
{
    public string SourceName{get;set;}="";
    public string Name{get;set;}="";
    public string SourceCategory{get;set;}="";
    public string Category{get;set;}="";
    public Dictionary<string,string> Tags{get;set;}=[];
    public string SourceReason{get;set;}="";
    public string Reason{get;set;}="";
}

/// <summary>Authored identity stays canonical. Display translations are asset metadata,
/// never a UI translation guess. Source stamps prevent obsolete translated names.</summary>
public static class AssetLocalization
{
    public static readonly string[] RequiredLanguages=["zh","en"];
    private static string Key(string language)=>language.Split('-','_')[0].ToLowerInvariant();
    private static AssetLocaleText? Text(MaterialAsset a,string language)=>a.Localizations.GetValueOrDefault(language)??a.Localizations.GetValueOrDefault(Key(language));
    public static string? TranslatedName(MaterialAsset a,string language)=>Text(a,language) is {} t&&t.SourceName==a.Name&&!string.IsNullOrWhiteSpace(t.Name)?t.Name:null;
    public static string Name(MaterialAsset a,string language)=>TranslatedName(a,language)??a.Name;
    public static string Category(MaterialAsset a,string language)=>Text(a,language) is {} t&&t.SourceCategory==a.Category&&!string.IsNullOrWhiteSpace(t.Category)?t.Category:a.Category;
    public static string Tag(MaterialAsset a,string tag,string language)=>Text(a,language)?.Tags.GetValueOrDefault(tag,tag)??tag;
    public static string Reason(MaterialAsset a,string language)=>Text(a,language) is {} t&&t.SourceReason==a.Randomization.Reason&&!string.IsNullOrWhiteSpace(t.Reason)?t.Reason:a.Randomization.Reason;
    public static bool Complete(MaterialAsset a)=>RequiredLanguages.All(lang=>
        Text(a,lang) is {} t&&t.SourceName==a.Name&&!string.IsNullOrWhiteSpace(t.Name)&&t.SourceCategory==a.Category&&
        (a.Category.Length==0||!string.IsNullOrWhiteSpace(t.Category))&&a.Tags.All(tag=>t.Tags.TryGetValue(tag,out var v)&&!string.IsNullOrWhiteSpace(v))&&
        (a.Plant!=null||a.Randomization.Reason.Length==0||t.SourceReason==a.Randomization.Reason&&!string.IsNullOrWhiteSpace(t.Reason)));
    public static bool Matches(MaterialAsset a,string query,string language)
    {
        string text=a.Name+" "+a.Category+" "+string.Join(" ",a.Tags)+" "+string.Join(" ",a.Localizations.Keys.Prepend(language).Distinct().Select(lang=>Name(a,lang)+" "+Category(a,lang)+" "+string.Join(" ",a.Tags.Select(t=>Tag(a,t,lang)))));
        return query.Trim().Split(' ',StringSplitOptions.RemoveEmptyEntries).All(w=>text.Contains(w,StringComparison.OrdinalIgnoreCase));
    }
    public static void Validate(MaterialAsset asset)
    {
        if(asset.Localizations.Count>16)throw new ArgumentException("Too many asset display languages.");
        foreach(var (lang,t) in asset.Localizations)
        {
            if(!Regex.IsMatch(lang,@"^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")||t==null||t.Tags==null||t.SourceName==null||t.Name==null||t.SourceCategory==null||t.Category==null||t.SourceReason==null||t.Reason==null||
                t.SourceName.Length>200||t.Name.Length>200||t.SourceCategory.Length>120||t.Category.Length>160||t.SourceReason.Length>4000||t.Reason.Length>4000||t.Tags.Count>64||t.Tags.Any(p=>string.IsNullOrWhiteSpace(p.Key)||p.Key.Length>120||string.IsNullOrWhiteSpace(p.Value)||p.Value.Length>160))
                throw new ArgumentException("Invalid asset language metadata.");
        }
    }
    public static void ValidateLabels(MaterialAsset asset,AssetLocaleLabel[] labels)
    {
        if(labels==null||labels.Length!=2||!labels.Select(l=>l.Language).ToHashSet().SetEquals(RequiredLanguages))throw new InvalidDataException("Complete Chinese and English asset labels are required.");
        foreach(var l in labels)
            if(string.IsNullOrWhiteSpace(l.Name)||l.Name.Length>200||l.Category==null||l.Category.Length>160||(asset.Category.Length>0&&string.IsNullOrWhiteSpace(l.Category))||l.Tags==null||l.Tags.Length!=asset.Tags.Length||l.Tags.Any(t=>string.IsNullOrWhiteSpace(t)||t.Length>160)||l.Reason==null||l.Reason.Length>4000||(asset.Plant==null&&asset.Randomization.Reason.Length>0&&string.IsNullOrWhiteSpace(l.Reason)))
                throw new InvalidDataException("Asset language labels do not match canonical fields.");
    }
    public static void SetDraft(MaterialAsset asset,AssetLocaleLabel[] labels,bool overwrite=true)
    {
        ValidateLabels(asset,labels);
        asset.Localizations??=[];
        foreach(var l in labels)
        {
            if(!asset.Localizations.TryGetValue(l.Language,out var t))asset.Localizations[l.Language]=t=new();
            if(overwrite||t.SourceName!=asset.Name||string.IsNullOrWhiteSpace(t.Name)){t.SourceName=asset.Name;t.Name=l.Name.Trim();}
            if(overwrite||t.SourceCategory!=asset.Category||string.IsNullOrWhiteSpace(t.Category)){t.SourceCategory=asset.Category;t.Category=l.Category.Trim();}
            foreach(var obsolete in t.Tags.Keys.Where(k=>!asset.Tags.Contains(k)).ToArray())t.Tags.Remove(obsolete);
            for(int i=0;i<asset.Tags.Length;i++)if(overwrite||!t.Tags.ContainsKey(asset.Tags[i]))t.Tags[asset.Tags[i]]=l.Tags[i].Trim();
            if(overwrite||t.SourceReason!=asset.Randomization.Reason||string.IsNullOrWhiteSpace(t.Reason)){t.SourceReason=asset.Randomization.Reason;t.Reason=l.Reason.Trim();}
        }
    }
    public static MaterialAsset[] Apply(MaterialLibrary library,MaterialAsset[] snapshot,CatalogLabel[] labels)=>library.Locked(()=>
    {
        if(labels.Length!=snapshot.Length||labels.Select(l=>l.Id).Distinct().Count()!=snapshot.Length||!labels.Select(l=>l.Id).ToHashSet().SetEquals(snapshot.Select(a=>a.Id)))throw new InvalidDataException("Localization must cover the exact asset snapshot.");
        var result=new List<MaterialAsset>();var changed=new List<MaterialAsset>();
        foreach(var old in snapshot)
        {
            var a=library.Get(old.Id);if(a.Revision!=old.Revision||a.CatalogRevision!=old.CatalogRevision)throw new InvalidOperationException("Asset metadata changed; retry localization.");
            var l=labels.Single(l=>l.Id==a.Id);
            if(l.Name!=a.Name||l.Category!=a.Category||!l.Tags.SequenceEqual(a.Tags))throw new InvalidDataException("Localization cannot rename or reorganize canonical fields.");
            string before=JsonSerializer.Serialize(a.Localizations,MaterialLibrary.Json);SetDraft(a,l.Localizations,false);a.Validate();
            if(before!=JsonSerializer.Serialize(a.Localizations,MaterialLibrary.Json)){a.CatalogRevision++;changed.Add(a);}result.Add(a);
        }
        if(changed.Count>0)library.CommitCatalog(changed.ToArray());return result.ToArray();
    });
    public static JsonObject LabelsSchema()=>new()
    {
        ["type"]="array",["items"]=new JsonObject
        {
            ["type"]="object",["additionalProperties"]=false,
            ["required"]=new JsonArray("language","name","category","tags","reason"),
            ["properties"]=new JsonObject
            {
                ["language"]=new JsonObject{["type"]="string",["enum"]=new JsonArray("zh","en")},
                ["name"]=new JsonObject{["type"]="string"},["category"]=new JsonObject{["type"]="string"},
                ["tags"]=new JsonObject{["type"]="array",["items"]=new JsonObject{["type"]="string"}},["reason"]=new JsonObject{["type"]="string"}
            }
        }
    };
    public const string Prompt="""
        LOCALIZED METADATA: For every labeled/organized/localized asset return localizations with exactly two entries, language zh and en. Each contains a natural concise name, category, tags (same count and exact semantic order as canonical tags), and reason (translation of the existing/randomization reason, or empty when unused). Preserve variant, test, synthetic and seasonal qualifiers; never invent measured properties. Canonical identity/name/category/tags remain independent from translated display text. Reuse existing translations of the same category/tag across the supplied catalog for consistency. Preserve nonempty valid existing translations in localize. Unknown botanical common names may use the existing Latin name. Never translate or change scientificName, family, genus, cultivar, IDs, sources, images or dimensions. No translated text changes filtering IDs. localize returns every supplied asset exactly once with canonical name/category/tags copied byte-for-byte; only localizations are new. Do not reorganize during localize. Do not claim image generation.
        """;
}
