using Eto.Drawing;
using Eto.Forms;
using System.Runtime.CompilerServices;
namespace RhinoSceneFlow.Plugin;

internal static class WorkspaceAppearance
{
    private static readonly ConditionalWeakTable<Control,LabelSource> originals=new();
    private sealed class LabelSource(string text){internal string Text=text;internal string Applied=text;}
    private static readonly Dictionary<string,string> english=new()
    {
        ["AI · 素材对话"]="AI · Assets",["材质库 · 浏览与应用"]="Materials · Library",["UV · 真实尺寸展开"]="UV · Physical scale",["植物库 · 种植"]="Plants · Library",["Plants List · 组合管理"]="Plants List · Groups",["属性 · 当前选择"]="Properties · Selection",["PSD · 视图导出"]="PSD · View export",["AI 后期 · Web 工作台"]="AI · Web studio",
        ["AI 素材对话"]="AI assets",["材质库"]="Material library",["植物库与种植"]="Planting",["组合参数"]="Group settings",["应用材质"]="Apply material",["应用选中材质"]="Apply selected material",["页面大小"]="Output size",["PSD 图层"]="PSD layers",["季节"]="Season",["季节版本"]="Seasonal variants",["跟随季节变化"]="Follow scene season",["跟随预览导出"]="Export preview season",["预览季节"]="Preview season",["预览"]="Preview",["细节调整"]="View adjustments",["导出此视图"]="Export this view",["输出文件夹"]="Output folder",["复制"]="Copy",["粘贴"]="Paste",["复制设置"]="Copy settings",["粘贴设置"]="Paste settings",["展开所有图层"]="Expand layers",["折叠所有图层"]="Collapse layers",["展开所有"]="Expand all",["折叠所有"]="Collapse all",["＋ 添加图层"]="+ Add layer",["导出勾选视图 · PSD"]="Export selected views · PSD",["取消导出"]="Cancel export",["导出日志"]="Export log",["生成／补齐四季"]="Generate missing seasons",["补齐夏季立面／平面"]="Complete summer elevation / plan",["取消季节任务"]="Cancel seasonal job",["优先查找已有素材"]="Find existing assets first",["浏览材质库"]="Material library",["浏览植物库"]="Plant library",["在 AI 对话中生成植物"]="Generate plants in AI chat",["刷新植物库"]="Refresh plant library",["加入组合 ↓"]="Add to palette",["放置植物"]="Place plants",["连续点种 · Esc 结束"]="Place continuously · Esc to finish",["在曲面上生成 / 重新关联"]="Scatter on surface / Rebind",["随机去重复"]="Random variation",["铺贴与外观设置"]="Mapping and appearance",["取消当前任务"]="Cancel task",["打开全局植物显示设置"]="Global plant display settings",["使用说明"]="Help"
    };
    internal static string Text(string value)=>PluginPreferences.Load().ResolvedLanguage=="en"&&english.TryGetValue(value,out var en)?en:value;
    internal static void Apply(Container root)
    {
        var p=PluginPreferences.Load();var bg=Rhino.ApplicationSettings.AppearanceSettings.GetPaintColor(Rhino.ApplicationSettings.PaintColor.PanelBackground);var fg=Rhino.ApplicationSettings.AppearanceSettings.GetPaintColor(Rhino.ApplicationSettings.PaintColor.TextEnabled);
        if(p.Theme!="rhino"){bg=p.Theme=="dark"?System.Drawing.Color.FromArgb(29,35,32):System.Drawing.Color.FromArgb(241,243,241);fg=p.Theme=="dark"?System.Drawing.Color.FromArgb(235,239,235):System.Drawing.Color.FromArgb(30,36,30);}
        var background=Color.FromArgb(bg.R,bg.G,bg.B);var foreground=Color.FromArgb(fg.R,fg.G,fg.B);
        foreach(var c in root.Children.Append(root))
        {
            if(c.IsDisposed||c is ImageView or PixelLayout)continue;
            if(c is Panel or Layout or Scrollable or GroupBox&&c.BackgroundColor!=background)c.BackgroundColor=background;
            var color=c.GetType().GetProperty("TextColor");if(color?.CanWrite==true&&color.PropertyType==typeof(Color)&&!foreground.Equals(color.GetValue(c)))color.SetValue(c,foreground);
            if(c is DropDown dropdown)
            {
                foreach(var item in dropdown.Items.OfType<ListItem>().Where(i=>!Guid.TryParse(i.Key,out _))){string source=english.ContainsKey(item.Text)?item.Text:english.FirstOrDefault(p=>p.Value==item.Text).Key??item.Text;string next=Text(source);if(item.Text!=next)item.Text=next;}
            }
            if(c.Tag as string!="user-content"&&c is Label or Button or CheckBox or GroupBox or Expander)
            {
                var prop=c.GetType().GetProperty(c is Expander?"Header":"Text");if(prop?.GetValue(c) is not string text)continue;
                var original=originals.GetValue(c,_=>new(text));if(original.Applied!=text){original.Text=text;original.Applied=text;}
                string next=Text(original.Text);if(next!=text){prop.SetValue(c,next);original.Applied=next;}
            }
        }
    }
}
