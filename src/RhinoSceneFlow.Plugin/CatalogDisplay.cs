using RhinoSceneFlow.Core;
namespace RhinoSceneFlow.Plugin;

/// <summary>Reads language metadata saved with each asset. Never translates canonical keys.</summary>
internal static class CatalogDisplay
{
    private static string Language=>UiPresentation.Preferences.ResolvedLanguage;
    internal static string Name(MaterialAsset a)=>AssetLocalization.Name(a,Language);
    internal static string Category(MaterialAsset a)=>AssetLocalization.Category(a,Language);
    internal static string Tag(MaterialAsset a,string tag)=>AssetLocalization.Tag(a,tag,Language);
    internal static string Reason(MaterialAsset a)=>a.Randomization.RecommendedBy=="none"&&a.Randomization.Reason=="尚未分析，可手动选择。"?WorkspaceAppearance.Text(a.Randomization.Reason):AssetLocalization.Reason(a,Language);
    internal static string SharedCategory(IEnumerable<MaterialAsset> assets,string key)=>assets.Select(Category).FirstOrDefault(t=>t!=key)??key;
    internal static string SharedTag(IEnumerable<MaterialAsset> assets,string key)=>assets.Select(a=>Tag(a,key)).FirstOrDefault(t=>t!=key)??key;
}
