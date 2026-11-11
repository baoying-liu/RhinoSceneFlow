using Eto.Drawing;
using Eto.Forms;
using System.Runtime.CompilerServices;
namespace RhinoSceneFlow.Plugin;

internal static class WorkspaceAppearance
{
    internal static readonly Dictionary<string,string> english=new()
    {
        ["按物种适生气候（默认）"]="Species' native climate (default)",["指定项目地区"]="Specify project location",["季节气候依据"]="Seasonal climate context",["项目地区"]="Project location",["例如：迈阿密，佛罗里达"]="e.g. Miami, Florida",["用于后续季节版本，不会自动重新生成已有图片。"]="Used for new seasonal variants; existing images stay unchanged.",
        ["将所有工具放入同一容器"]="Group all tools in this sidebar",["工作区布局"]="Workspace layout",
        ["跟随 Rhino"]="Follow Rhino",["浅色"]="Light",["深色"]="Dark",["自动切换"]="Automatic",["立面 · 沿 Z 轴"]="Elevation · Z axis",["立面 · 朝向相机"]="Elevation · Face camera",["平面图"]="Plan",
        ["宽度 mm"]="Width mm",["高度 mm"]="Height mm",["不透明度 %"]="Opacity %",
        ["界面文字"]="Interface text",["界面图标"]="Interface icons",["必要文字（无文字模式）"]="Essential text (icon mode)",
        ["全称"]="Full",["缩写"]="Abbreviated",["无"]="None",["显示"]="Show",
        ["至少保留文字或图标。素材名、输入值和状态仍显示；悬停查看全称。设置影响 Rhino 工具页，不改写素材或网页内容。"]="Keep text or icons visible. Names, values and status remain readable; hover for full labels. Applies to Rhino tools, not asset data or web content.",
        ["显示语言"]="Display language",
        ["界面主题"]="Interface theme",
        ["影响 Rhino 侧栏和素材对话；Web 工作台有独立的语言设置。"]="Applies to Rhino panels and asset chat. Web Studio has its own language setting.",
        ["恢复界面默认"]="Reset interface defaults",
        ["气候与地区"]="Climate and region",
        ["默认生成四季版本"]="Generate all seasons by default",
        ["默认生成夏季；植物同时补齐立面和平面。缺失版本回退夏季。"]="Summer is the default. Plants get elevation and plan images. Missing variants fall back to summer.",
        ["恢复生成默认"]="Reset generation defaults",
        ["朝向模式"]="Facing mode",
        ["按镜头俯角切换：水平 0°，正俯视 90°。"]="Switches by camera elevation: horizontal 0°, top-down 90°.",
        ["自由朝向中心角 · °"]="Free-facing centre · °",
        ["过渡半宽 · °"]="Transition half-width · °",
        ["平面图起始角 · °"]="Plan starts at · °",
        ["平面抬升比例 · 实际树高 × 比例"]="Plan lift · actual tree height × ratio",
        ["自动：低角度沿 Z 轴，过渡后朝向相机，高俯视使用平面。平面缺失时暂用立面。"]="Auto: Z axis at low angles, face camera after transition, plan at high angles. Missing plans use elevation temporarily.",
        ["恢复植物显示默认"]="Reset plant display defaults",
        ["设置"]="Settings",
        ["全局设置 · 所有 Rhino 文件共用"]="Global settings · shared by all Rhino documents",
        ["界面"]="Interface",
        ["素材生成"]="Asset generation",
        ["植物显示"]="Plant display",
        ["保存设置"]="Save settings",
        ["还原未保存修改"]="Discard unsaved changes",
        ["设置已保存到本机。"]="Settings saved on this computer.",
        ["有未保存修改"]="Unsaved changes",
        ["已保存 · 当前场景已刷新"]="Saved · current scene refreshed",
        ["未保存："]="Not saved: ",
        ["设置 · SceneFlow"]="Settings · SceneFlow",["包含植物透空投影"]="Include alpha-cutout plant shadows",["分离植物阴影"]="Separate plant shadows",["分离后放在植物组最底层，沿用阴影通道的混合、透明度和眼睛；未启用植物通道时仍合并导出。"]="Placed below all foliage in the Plants group; uses the shadow pass blend, opacity and visibility. Without a Plants pass, shadows stay combined.",
        ["AI · 素材对话"]="AI · Assets",["材质库 · 浏览与应用"]="Materials · Library",["UV · 真实尺寸展开"]="UV · Physical scale",["植物库 · 种植"]="Plants · Library",["Plants List · 组合管理"]="Plants List · Groups",["属性 · 当前选择"]="Properties · Selection",["PSD · 视图导出"]="PSD · View export",["AI 后期 · Web 工作台"]="AI · Web studio",
        ["AI 素材对话"]="AI assets",["材质库"]="Material library",["植物库与种植"]="Planting",["组合参数"]="Group settings",["应用材质"]="Apply material",["应用选中材质"]="Apply selected material",["页面大小"]="Output size",["PSD 图层"]="PSD layers",["季节"]="Season",["季节版本"]="Seasonal variants",["跟随季节变化"]="Follow scene season",["跟随预览导出"]="Export preview season",["预览季节"]="Preview season",["预览"]="Preview",["细节调整"]="View adjustments",["导出此视图"]="Export this view",["输出文件夹"]="Output folder",["复制"]="Copy",["粘贴"]="Paste",["复制设置"]="Copy settings",["粘贴设置"]="Paste settings",["展开所有图层"]="Expand layers",["折叠所有图层"]="Collapse layers",["展开所有"]="Expand all",["折叠所有"]="Collapse all",["＋ 添加图层"]="+ Add layer",["导出勾选视图 · PSD"]="Export selected views · PSD",["取消导出"]="Cancel export",["导出日志"]="Export log",["生成／补齐四季"]="Generate missing seasons",["补齐夏季立面／平面"]="Complete summer elevation / plan",["取消季节任务"]="Cancel seasonal job",["优先查找已有素材"]="Find existing assets first",["浏览材质库"]="Material library",["浏览植物库"]="Plant library",["在 AI 对话中生成植物"]="Generate plants in AI chat",["刷新植物库"]="Refresh plant library",["加入组合 ↓"]="Add to palette",["放置植物"]="Place plants",["连续点种 · Esc 结束"]="Place continuously · Esc to finish",["在曲面上生成 / 重新关联"]="Scatter on surface / Rebind",["随机去重复"]="Random variation",["铺贴与外观设置"]="Mapping and appearance",["取消当前任务"]="Cancel task",["打开全局植物显示设置"]="Global plant display settings",["使用说明"]="Help"
    };
    internal static string Text(string value)=>NativeText.Translate(value,PluginPreferences.Load().ResolvedLanguage);
    private static void WrapCaption(object? caption)
    {
        if(caption==null)return;
        var wrapping=caption.GetType().GetProperty("TextWrapping");
        if(wrapping?.CanWrite==true&&wrapping.PropertyType==typeof(System.Windows.TextWrapping))wrapping.SetValue(caption,System.Windows.TextWrapping.Wrap);
        if(caption is System.Windows.Controls.Panel panel)foreach(var child in panel.Children)WrapCaption(child);
        else if(caption is System.Windows.Controls.ContentControl content)WrapCaption(content.Content);
    }
    internal static void Apply(Container root)
    {
        var p=PluginPreferences.Load();var bg=Rhino.ApplicationSettings.AppearanceSettings.GetPaintColor(Rhino.ApplicationSettings.PaintColor.PanelBackground);var fg=Rhino.ApplicationSettings.AppearanceSettings.GetPaintColor(Rhino.ApplicationSettings.PaintColor.TextEnabled);
        if(p.Theme!="rhino"){bg=p.Theme=="dark"?System.Drawing.Color.FromArgb(29,35,32):System.Drawing.Color.FromArgb(241,243,241);fg=p.Theme=="dark"?System.Drawing.Color.FromArgb(235,239,235):System.Drawing.Color.FromArgb(30,36,30);}
        var background=Color.FromArgb(bg.R,bg.G,bg.B);var foreground=Color.FromArgb(fg.R,fg.G,fg.B);
        foreach(var c in root.Children.Append(root))
        {
            if(c.IsDisposed||c is ImageView or PixelLayout)continue;
            // EtoAccessLabel exposes wrapping publicly, but Eto Button/CheckBox
            // do not. Keep their handler-owned caption and mnemonic behavior.
            if(c is Button or CheckBox && c.ControlObject is System.Windows.Controls.ContentControl native && native.Content is {} caption)
            {
                var wrapping=caption.GetType().GetProperty("TextWrapping");
                if(wrapping?.CanWrite==true&&wrapping.PropertyType==typeof(System.Windows.TextWrapping))
                    wrapping.SetValue(caption,System.Windows.TextWrapping.Wrap);
            }

            if(c is Panel or Layout or Scrollable or GroupBox&&c.BackgroundColor!=background)c.BackgroundColor=background;
            var color=c.GetType().GetProperty("TextColor");if(color?.CanWrite==true&&color.PropertyType==typeof(Color)&&!foreground.Equals(color.GetValue(c)))color.SetValue(c,foreground);
            if(c is SeasonalAssetPanel seasonal)seasonal.RefreshLanguage(p.ResolvedLanguage);
            if(c is Button button){WrapCaption((button.ControlObject as System.Windows.Controls.ContentControl)?.Content);InterfacePresentation.NormalizeIconVisual(button);}

        }
        foreach(var c in root.Children)InterfacePresentation.Layout(c,p);
    }
}
