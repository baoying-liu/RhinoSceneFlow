using System.Text.Json;
using Rhino.ApplicationSettings;
using RhinoSceneFlow.Core;
namespace RhinoSceneFlow.Plugin;

public sealed class PlantUiPreferences
{
    public string Language {get;set;}="auto";
    public string LibraryView {get;set;}="tiles";
    public string CompositionView {get;set;}="tiles";
    public string ResolvedLanguage=>PluginPreferences.Load().ResolvedLanguage;
    internal static PlantUiPreferences Load()=>JsonSerializer.Deserialize<PlantUiPreferences>(SceneFlowPlugin.Instance.Settings.GetString("PlantUiPreferences","{}"),MaterialLibrary.Json)!;
    internal static PlantUiPreferences Save(PlantUiPreferences value)
    {
        if(value.Language is not("auto" or "zh" or "en")||value.LibraryView is not("tiles" or "list")||value.CompositionView is not("tiles" or "list"))throw new ArgumentException("植物名称语言或视图模式无效。");
        SceneFlowPlugin.Instance.Settings.SetString("PlantUiPreferences",JsonSerializer.Serialize(value,MaterialLibrary.Json));SceneFlowPlugin.Instance.SaveSettings();PlantTool.PresentationChanged();return value;
    }
}
