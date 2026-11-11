using System.Text.Json;
using System.Text.Json.Serialization;
using Eto.Forms;
using Rhino;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class PluginPreferences
{
    public string Language{get;set;}="auto";
    public string Theme{get;set;}="rhino";
    public string TextMode{get;set;}="full";
    public bool ShowIcons{get;set;}=true;
    public string EssentialTextMode{get;set;}="short";
    public string Season{get;set;}="summer";
    public string? ClimateMode{get;set;}
    public string Climate{get;set;}="";
    [JsonIgnore]public string GenerationClimate=>ClimateContext.Resolve(ClimateMode,Climate).Instruction;
    [JsonIgnore]public string ClimateMetadata=>ClimateContext.Resolve(ClimateMode,Climate).Metadata;
    public bool GenerateFourSeasons{get;set;}
    public string ResolvedLanguage=>Language=="auto"?(Rhino.ApplicationSettings.AppearanceSettings.LanguageIdentifier&1023)==4?"zh":"en":Language;
    private static PluginPreferences Normalize(PluginPreferences p){var c=ClimateContext.Resolve(p.ClimateMode,p.Climate);p.ClimateMode=c.Mode;p.Climate=c.Location;return p;}
    public static PluginPreferences Load()=>Normalize(JsonSerializer.Deserialize<PluginPreferences>(SceneFlowPlugin.Instance.Settings.GetString("PreferencesSeasonal","{}"),MaterialLibrary.Json)!);
    public static PluginPreferences Save(PluginPreferences p)
    {
        Normalize(p);
        if(p.TextMode is not ("full" or "short" or "none") || p.EssentialTextMode is not ("full" or "short") || (!p.ShowIcons && p.TextMode=="none"))
            throw new ArgumentException("Choose text or icons; both cannot be hidden.");
        if(p.Language is not ("auto" or "zh" or "en")||p.Theme is not ("rhino" or "light" or "dark"))throw new ArgumentException("Invalid preferences.");Seasons.Validate(p.Season);
        var previous=Load();
        SceneFlowPlugin.Instance.Settings.SetString("PreferencesSeasonal",JsonSerializer.Serialize(p,MaterialLibrary.Json));SceneFlowPlugin.Instance.SaveSettings();
        if(previous.Season!=p.Season)PlantService.RefreshSeasons();
        UiPresentation.Refresh(p);
        if(previous.ResolvedLanguage!=p.ResolvedLanguage)PlantTool.PresentationChanged();
        SceneFlowWorkspace.RefreshAppearance(p);return p;
    }
    // Compatibility entry points all navigate to the same dockable settings page.
    public static void Show()=>SceneFlowWorkspace.Open("settings");
}
