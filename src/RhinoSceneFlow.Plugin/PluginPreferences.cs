using System.Text.Json;
using Eto.Forms;
using Rhino;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

public sealed class PluginPreferences
{
    public string Language{get;set;}="auto";
    public string Theme{get;set;}="rhino";
    public string Season{get;set;}="summer";
    public string Climate{get;set;}="依照已核实物种的适生气候";
    public bool GenerateFourSeasons{get;set;}
    public string ResolvedLanguage=>Language=="auto"?(Rhino.ApplicationSettings.AppearanceSettings.LanguageIdentifier&1023)==4?"zh":"en":Language;
    public static PluginPreferences Load()=>JsonSerializer.Deserialize<PluginPreferences>(SceneFlowPlugin.Instance.Settings.GetString("PreferencesSeasonal","{}"),MaterialLibrary.Json)!;
    public static PluginPreferences Save(PluginPreferences p)
    {
        if(p.Language is not ("auto" or "zh" or "en")||p.Theme is not ("rhino" or "light" or "dark")||p.Climate.Length>300)throw new ArgumentException("Invalid preferences.");Seasons.Validate(p.Season);
        SceneFlowPlugin.Instance.Settings.SetString("PreferencesSeasonal",JsonSerializer.Serialize(p,MaterialLibrary.Json));SceneFlowPlugin.Instance.SaveSettings();PlantService.RefreshSeasons();PlantTool.PresentationChanged();return p;
    }
    public static void Show()
    {
        var p=Load();var billboards=PlantService.Settings;
        using var dialog=new Dialog{Title="SceneFlow · 设置 / Settings",ClientSize=new(520,490),Resizable=true,Padding=new(14)};
        DropDown Choices(params (string Key,string Name)[] choices){var d=new DropDown();foreach(var c in choices)d.Items.Add(new ListItem{Key=c.Key,Text=c.Name});return d;}
        var language=Choices(("auto","跟随 Rhino / Follow Rhino"),("zh","中文"),("en","English"));language.SelectedKey=p.Language;
        var theme=Choices(("rhino","跟随 Rhino / Follow Rhino"),("dark","深色 / Dark"),("light","浅色 / Light"));theme.SelectedKey=p.Theme;
        var climate=new TextBox{Text=p.Climate};var four=new CheckBox{Text="默认补齐四季 / Generate all seasons",Checked=p.GenerateFourSeasons};
        var general=Ui.Layout();general.AddRow(ToolUi.Note("语言 / Language"));general.AddRow(language);general.AddRow(ToolUi.Note("主题 / Theme"));general.AddRow(theme);general.AddRow(ToolUi.Note("气候地区 / Climate"));general.AddRow(climate);general.AddRow(four);
        general.AddRow(ToolUi.Note("素材默认夏季；四季缺少的版本回退夏季，不修改太阳日期。 / Missing variants fall back to summer; sun date stays independent."));
        var mode=Choices(("auto","自动 / Auto"),("z","立面 · Z 轴 / Z axis"),("free","立面 · 自由 / Face camera"),("plan","平面 / Plan"));mode.SelectedKey=billboards.Mode;
        var angle=Ui.Number(10,80);angle.Value=billboards.Angle;var plan=Ui.Number(20,90);plan.Value=billboards.PlanAngle;var transition=Ui.Number(1,15);transition.Value=billboards.Transition;var ratio=Ui.Number(0,2,2);ratio.Value=billboards.PlanHeightRatio;
        var plants=Ui.Layout();plants.AddRow(ToolUi.Note("水平看为 0°，正俯视为 90° / Horizontal 0°, top-down 90°"));plants.AddRow(mode);
        plants.AddRow(ToolUi.Note("开始自由朝向 / Free-facing angle"));plants.AddRow(angle);plants.AddRow(ToolUi.Note("朝向过渡缓冲 / Transition"));plants.AddRow(transition);plants.AddRow(ToolUi.Note("切换平面 / Plan angle"));plants.AddRow(plan);plants.AddRow(ToolUi.Note("平面抬升 / Height × scale × ratio"));plants.AddRow(ratio);
        plants.AddRow(Ui.Button("恢复默认 / Reset",()=>{var d=new BillboardSettings();mode.SelectedKey=d.Mode;angle.Value=d.Angle;plan.Value=d.PlanAngle;transition.Value=d.Transition;ratio.Value=d.PlanHeightRatio;}));
        var tabs=new TabControl();tabs.Pages.Add(new TabPage{Text="常规 / General",Content=general});tabs.Pages.Add(new TabPage{Text="植物显示 / Plants",Content=plants});
        var error=ToolUi.Note("");var root=Ui.Layout();root.Add(tabs,true,true);root.AddRow(error);
        root.AddRow(ToolUi.Pair(Ui.Button("保存 / Save",()=>{try{var b=new BillboardSettings{Mode=mode.SelectedKey!,Angle=angle.Value,PlanAngle=plan.Value,Transition=transition.Value,PlanHeightRatio=ratio.Value};b.Validate();p.Language=language.SelectedKey!;p.Theme=theme.SelectedKey!;p.Climate=climate.Text;p.GenerateFourSeasons=four.Checked==true;Save(p);PlantService.Settings=b;dialog.Close();}catch(Exception e){error.Text=e.Message;}}),Ui.Button("取消 / Cancel",()=>dialog.Close())));dialog.Content=root;dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow);
    }
}
