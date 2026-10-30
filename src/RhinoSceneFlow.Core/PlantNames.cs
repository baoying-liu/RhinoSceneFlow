namespace RhinoSceneFlow.Core;

public static class PlantNames
{
    public static string Display(MaterialAsset asset,string language)
    {
        var p=asset.Plant??throw new ArgumentException("Not a plant.");string key=language.StartsWith("zh",StringComparison.OrdinalIgnoreCase)?"zh":"en";
        if(p.Names.TryGetValue(key,out var value)&&!string.IsNullOrWhiteSpace(value))return value;
        bool han=asset.Name.Any(c=>c is >= '\u3400' and <= '\u9fff');
        return (key=="zh"&&han)||(key=="en"&&!han)?asset.Name:p.ScientificName;
    }
    public static void Apply(MaterialLibrary library,MaterialAsset[] snapshot,PlantNameLabel[] labels)=>library.Locked(()=>
    {
        if(labels.Length!=snapshot.Length||labels.Select(l=>l.Id).Distinct().Count()!=labels.Length||labels.Any(l=>!snapshot.Any(a=>a.Id==l.Id)||string.IsNullOrWhiteSpace(l.Zh)||string.IsNullOrWhiteSpace(l.En)||l.Zh.Length>100||l.En.Length>100))throw new ArgumentException("植物中英文名称方案不完整。");
        var current=snapshot.Select(old=>
        {
            var a=library.Get(old.Id);if(a.Revision!=old.Revision||a.CatalogRevision!=old.CatalogRevision)throw new InvalidOperationException("植物库已更新，请重试名称补全。");
            var label=labels.Single(l=>l.Id==a.Id);var p=a.Plant??throw new ArgumentException("Not a plant.");
            if(!p.Names.TryGetValue("zh",out var zh)||string.IsNullOrWhiteSpace(zh))p.Names["zh"]=label.Zh.Trim();
            if(!p.Names.TryGetValue("en",out var en)||string.IsNullOrWhiteSpace(en))p.Names["en"]=label.En.Trim();
            a.CatalogRevision++;a.Validate();return a;
        }).ToArray();library.CommitCatalog(current);return true;
    });
}
