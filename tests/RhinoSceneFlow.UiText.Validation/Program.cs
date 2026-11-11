using System.Text.Json;
using RhinoSceneFlow.Plugin;
static void Equal(string expected,string? actual,string name){if(expected!=actual)throw new Exception(name+": "+actual+" != "+expected);}
using var data=typeof(NativeText).Assembly.GetManifestResourceStream("RhinoSceneFlow.Plugin.Resources.NativeText.json")!;
using var json=JsonDocument.Parse(data);int count=0;
foreach(var entry in json.RootElement.EnumerateArray())
{
    string zh=entry.GetProperty("zh").GetString()!,en=entry.GetProperty("en").GetString()!;
    if(zh.Contains("{0}"))continue;
    Equal(en,NativeText.Translate(zh,"en"),"English "+zh);
    Equal(en,NativeText.Translate(en,"en"),"English stable "+en);
    string shortEn=entry.GetProperty("shortEn").GetString()!;
    if(shortEn.Length>0)Equal(shortEn,NativeText.Short(en),"Short "+en);
    count++;
}
Equal("12 materials",NativeText.Translate("12 个材质","en"),"Count");
Equal("12 mats",NativeText.Short("12 materials"),"Short count");
Equal("Variation · Off",NativeText.Translate("去重复 · 关闭","en"),"Enum context");
Equal("4 × 8 source repeats",NativeText.Translate("4 × 8 个原图周期","en"),"Two placeholders");
Equal("15 plants · Manual 4 · Target 15",NativeText.Translate("15 株 · 手工 4 · 目标 15","en"),"Plant summary");
Equal("15 plants · Manual 4 · Target 15 · Spacing / edge limits prevented filling",NativeText.Translate("15 株 · 手工 4 · 目标 15 · 间距／边缘限制未填满","en"),"Specific status before generic");
Equal("红枫 A · Individual plant",NativeText.Translate("红枫 A · 单株","en"),"User name in contextual title");
Equal("World UV",NativeText.Short("Physical-scale UVs"),"UV abbreviation");
Equal("自定义资产 Betula 测试",NativeText.Translate("自定义资产 Betula 测试","en"),"User text unchanged");
if(args.Length>0)
{
    using var snapshot=JsonDocument.Parse(File.ReadAllText(args[0]));int checkedLabels=0;
    foreach(var row in snapshot.RootElement.GetProperty("rows").EnumerateArray())
    {
        string text=row.GetProperty("text").GetString()??"";
        string translated=NativeText.Translate(text,"en");
        if(System.Text.RegularExpressions.Regex.IsMatch(translated,@"[\u4e00-\u9fff]"))throw new Exception("Untranslated UI caption: "+text);
        checkedLabels++;
    }
    Console.WriteLine($"PASS: {checkedLabels} captured native captions translated without Chinese leakage.");
}
Console.WriteLine($"PASS: {count} full English captions, semantic abbreviations, dynamic counts/enums and user text preservation.");
namespace RhinoSceneFlow.Plugin {internal static class WorkspaceAppearance {internal static readonly Dictionary<string,string> english=new();}}
