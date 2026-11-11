using Eto.Forms;
using Eto.Drawing;
using System.Runtime.CompilerServices;
using System.Text.RegularExpressions;
namespace RhinoSceneFlow.Plugin;

/// <summary>Presentation only: never abbreviate editable values or library/document names.
/// Unknown specialised captions retain essential text instead of acquiring an ambiguous icon.</summary>
internal static class InterfacePresentation
{
    private sealed class State(Control control)
    {
        internal readonly int Width=PreferredWidth(control);
        internal readonly System.Windows.HorizontalAlignment Alignment=(control.ControlObject as System.Windows.FrameworkElement)?.HorizontalAlignment??System.Windows.HorizontalAlignment.Stretch;
        internal Image? OriginalImage=(control as Button)?.Image, AppliedImage;
    }
    // Eto Width reads measured size (zero for an unarranged/collapsed control),
    // not its requested width. Preserve the WPF preferred width instead.
    private static int PreferredWidth(Control control)=>control.ControlObject is System.Windows.FrameworkElement n&&double.IsFinite(n.Width)?(int)Math.Round(n.Width):-1;
    private static readonly ConditionalWeakTable<Control,State> states=new();
    private static readonly Dictionary<string,Bitmap> images=new();
    private static readonly (string Pattern,string Icon)[] actions=[
        (@"^(⚙|设置|界面与名称|Settings|Global.*settings|打开全局)","settings"),
        (@"^(⋯|更多|More)","ellipsis"),
        (@"^(复制|Copy)","copy"),(@"^(粘贴|Paste)","clipboard-paste"),
        (@"^(刷新|Refresh|重新加载|Reload|↻)","refresh-cw"),
        (@"^(恢复|还原|重置|Reset|Discard|Undo)","undo-2"),
        (@"^(保存|Save)","save"),(@"^(取消|停止|Cancel|Stop)","circle-stop"),
        (@"^(删除|移除|清除|Delete|Remove|Clear|×|✕)$|^(删除|移除|清除|Delete |Remove |Clear )","x"),
        (@"^(↑|上移|Move up)$","chevron-up"),(@"^(↓|下移|Move down)$","chevron-down"),
        (@"^(展开|Expand)","chevron-down"),(@"^(折叠|Collapse)","chevron-up"),
        (@"^(导出|前往 PSD|Export|下载|Download|发送所选 PSD|Send selected PSD)","file-output"),
        (@"^(导入|Import|从本机选择|选择其他|选择文件|浏览|Browse|Choose|Select.*file)","folder-open"),
        (@"^(搜索|查找|Search|Find)","search"),
        (@"^(加入|添加|新建|创建|[＋+]|Add|New|Create)","plus"),
        (@"^(材质库|Material library|Materials.*Library)","swatch-book"),
        (@"^(植物库|Plant library|Plants.*Library|放置|连续点种|Place|Scatter|在曲面上)","trees"),
        (@"^(Plants List|组合管理|Group settings)","list-tree"),
        (@"^(准备.*UV|更新.*UV|打开 UV|真实尺寸 UV|UV|Physical)","grid-3x3"),
        (@"^(AI.*素材|AI.*Assets|在 AI|Generate.*chat)","message-square-more"),
        (@"^(打开 Web|打开 AI 渲染|Open Web|Open AI render|AI.*Web)","image"),
        (@"^(应用|Apply|确认|Confirm|完成|结束|Finish|Done)","check"),
        (@"^(生成|补齐|Generate|Complete|AI 整理)","wand-sparkles"),
        (@"^(编辑|进入单株|Edit)","sliders-horizontal"),
        (@"^(显示全部|Zoom|定位|在画布中|Show in)","maximize-2")];
    private static readonly Dictionary<string,string> shortNames=new(StringComparer.OrdinalIgnoreCase)
    {
        ["编辑组合"]="编辑",["定位到组合"]="定位",["完成并退出单株编辑"]="完成编辑",["当前选择的属性"]="选择属性",
        ["修改范围"]="范围",["材质名称（多个值时留空）"]="材质名",["植物类型 · 更换时保留当前高度"]="植物类型",["相对素材大小"]="相对大小",
        ["更新真实尺寸 UV"]="更新 UV",["准备 / 更新 UV"]="准备 UV",["应用材质修改"]="应用修改",["保存单株设置"]="保存单株",
        ["在视口中移动 · 吸附承载面"]="吸附移动",["返回组合设置"]="返回组合",["结束单株编辑"]="结束编辑",["进入单株编辑"]="编辑单株",
        ["保存尺寸与外观参数"]="保存外观",["打开 UV 工具"]="UV 工具",["保存并应用随机设置"]="应用去重复",["取消后续步骤"]="取消",
        ["应用到当前物件"]="当前物件",["应用到物件所在图层"]="所在图层",["相同材质合并（默认）"]="按材质合并",["按学名合并（默认）"]="按学名合并",
        ["Scatter on surface / Rebind"]="Scatter / Rebind",["在曲面上生成 / 重新关联"]="散布 / 关联",
        ["AI · Assets"]="AI",["AI · 素材对话"]="AI",["Materials · Library"]="Materials",["材质库 · 浏览与应用"]="材质库",
        ["UV · Physical scale"]="UV",["UV · 真实尺寸展开"]="UV",["Plants · Library"]="Plants",["植物库 · 种植"]="植物库",
        ["Plants List · Groups"]="Groups",["Plants List · 组合管理"]="组合",["Properties · Selection"]="Properties",["属性 · 当前选择"]="属性",
        ["PSD · View export"]="PSD",["PSD · 视图导出"]="PSD",["AI · Web studio"]="Studio",["AI 后期 · Web 工作台"]="工作台",
        ["Settings · SceneFlow"]="Settings",["设置 · SceneFlow"]="设置",
        ["Display language"]="Language",["显示语言"]="语言",["Interface theme"]="Theme",["界面主题"]="主题",
        ["Interface text"]="Text",["界面文字"]="文字",["Interface icons"]="Icons",["界面图标"]="图标",
        ["Essential text (icon mode)"]="Essential text",["必要文字（无文字模式）"]="必要文字",
        ["Abbreviated"]="Short",["缩写"]="缩写",["Follow Rhino"]="Rhino",["跟随 Rhino"]="Rhino",
        ["Automatic"]="Auto",["自动切换"]="自动",["Physical scale"]="UV scale",["真实尺寸 UV"]="UV 尺寸",
        ["Output folder"]="Folder",["输出文件夹"]="文件夹",["Output size"]="Size",["页面大小"]="尺寸",
        ["Preview season"]="Season",["预览季节"]="季节",["Global settings · shared by all Rhino documents"]="Shared across documents",["全局设置 · 所有 Rhino 文件共用"]="所有文件共用",
        ["Preview"]="Preview",["不透明度 %"]="透明度 %",["Opacity %"]="Opacity %",
        ["Reset interface defaults"]="Reset UI",["恢复界面默认"]="重置界面",["Save settings"]="Save",["保存设置"]="保存",
        ["Discard unsaved changes"]="Discard",["还原未保存修改"]="放弃修改",["Generate all seasons by default"]="All seasons",["默认生成四季版本"]="生成四季",
        ["Seasonal climate context"]="Climate source",["季节气候依据"]="气候依据",["Species' native climate (default)"]="Native climate",["按物种适生气候（默认）"]="物种气候",
        ["Specify project location"]="Project location",["指定项目地区"]="项目地区",["Free-facing centre · °"]="Facing angle · °",["自由朝向中心角 · °"]="自由角 · °",
        ["Transition half-width · °"]="Transition · °",["过渡半宽 · °"]="过渡 · °",["Plan starts at · °"]="Plan angle · °",["平面图起始角 · °"]="平面角 · °",
        ["Plan lift · actual tree height × ratio"]="Plan lift / height",["平面抬升比例 · 实际树高 × 比例"]="平面抬升 / 树高",
        ["Elevation · Z axis"]="Z axis",["立面 · 沿 Z 轴"]="Z 轴",["Elevation · Face camera"]="Face camera",["立面 · 朝向相机"]="朝向镜头",
        ["Include alpha-cutout plant shadows"]="Plant cutouts",["包含植物透空投影"]="植物镂空影",["Separate plant shadows"]="Separate plants",["分离植物阴影"]="分离植物影",
        ["Generate plants in AI chat"]="AI plants",["在 AI 对话中生成植物"]="AI 植物",["Find existing assets first"]="Reuse first",["优先查找已有素材"]="优先复用",
        ["Apply selected material"]="Apply material",["应用选中材质"]="应用材质",["Export selected views · PSD"]="Export PSD",["导出勾选视图 · PSD"]="导出 PSD",
        ["Continuous placement · Esc to finish"]="Place · Esc ends",["连续点种 · Esc 结束"]="点种 · Esc 结束"
    };
    internal static string Short(string text)
    {
        if(NativeText.Short(text) is {} localized)return localized;
        if(shortNames.TryGetValue(text,out var s))return s;
        // Whole semantic phrases only: no character truncation, ellipses or lost units.
        var pairs=new[]{("Copy settings","Copy"),("Paste settings","Paste"),("Refresh file list","Refresh"),("Open Web Studio","Open Studio"),("Expand all layers","Expand layers"),("Collapse all layers","Collapse layers"),("复制设置","复制"),("粘贴设置","粘贴"),("刷新文件列表","刷新"),("打开 Web 工作台","打开工作台"),("恢复默认设置","重置"),("展开所有图层","展开图层"),("折叠所有图层","折叠图层"),("随机去重复","去重复"),("尺寸与高级设置","尺寸 / 高级")};
        foreach(var (full,shorter) in pairs)if(text.Equals(full,StringComparison.OrdinalIgnoreCase))return shorter;
        return text;
    }
    private static readonly (Regex Pattern,string Icon)[] rules=actions.Select(a=>(new Regex(a.Pattern,RegexOptions.IgnoreCase|RegexOptions.CultureInvariant),a.Icon)).ToArray();
    private static readonly Dictionary<string,string?> iconNames=new();
    private static string? Icon(string text)
    {
        text=NativeText.Canonical(text);
        if(iconNames.TryGetValue(text,out var known))return known;
        return iconNames[text]=rules.FirstOrDefault(a=>a.Pattern.IsMatch(text)).Icon;
    }
    internal static void NormalizeIconVisual(Button button)
    {
        void Walk(object? visual)
        {
            if(visual is System.Windows.Controls.Image image)
            {
                image.Width=image.Height=16;image.MaxWidth=image.MaxHeight=16;
                image.Stretch=System.Windows.Media.Stretch.Uniform;
                image.StretchDirection=System.Windows.Controls.StretchDirection.DownOnly;
                image.HorizontalAlignment=System.Windows.HorizontalAlignment.Center;
                image.VerticalAlignment=System.Windows.VerticalAlignment.Center;
                image.SnapsToDevicePixels=true;return;
            }
            if(visual is System.Windows.Controls.Panel panel)foreach(var child in panel.Children)Walk(child);
            else if(visual is System.Windows.Controls.ContentControl content)Walk(content.Content);
            else if(visual is System.Windows.Controls.Decorator border)Walk(border.Child);
        }
        Walk(button.ControlObject);
    }
    private static Bitmap? Image(string name,bool dark)
    {
        string key=name+(dark?"-dark-32":"-light-32");if(images.TryGetValue(key,out var cached))return cached;
        using var stream=typeof(InterfacePresentation).Assembly.GetManifestResourceStream("RhinoSceneFlow.Plugin.Resources.InterfaceIcons."+key+".png");
        if(stream==null)return null;return images[key]=new Bitmap(stream);
    }
    internal static string Caption(Control c,string full,PluginPreferences p,Color foreground,string? hintSource=null)
    {
        if(c.Tag as string=="user-content")return full;
        var state=states.GetValue(c,x=>new State(x));


        if(c is Button && string.IsNullOrWhiteSpace(full) && !p.ShowIcons && !string.IsNullOrWhiteSpace(hintSource))
            full=hintSource.Contains("PSD 中可见")?(p.ResolvedLanguage=="zh"?"可见":"Visible"):
                 hintSource.Contains("PSD 中隐藏")?(p.ResolvedLanguage=="zh"?"隐藏":"Hidden"):WorkspaceAppearance.Text(hintSource);
        string symbol=full;bool symbolic=full is "⚙" or "⋯" or "↑" or "↓" or "×" or "↻";
        if(symbolic)full=full switch{
            "⚙"=>p.ResolvedLanguage=="zh"?"设置":"Settings",
            "⋯"=>p.ResolvedLanguage=="zh"?"更多":"More",
            "↑"=>p.ResolvedLanguage=="zh"?"上移":"Up",
            "↓"=>p.ResolvedLanguage=="zh"?"下移":"Down",
            "↻"=>p.ResolvedLanguage=="zh"?"刷新":"Refresh",
            _=>p.ResolvedLanguage=="zh"?"删除":"Remove"};
        string label=p.TextMode=="full"?full:Short(full);
        if(c is Button button)
        {
            if(button.Image!=state.AppliedImage)state.OriginalImage=button.Image;
            string? icon=Icon(symbolic?symbol:full);
            // Existing specialised imagery (for example PSD visibility) has priority.
            var image=p.ShowIcons?(state.OriginalImage??(icon==null?null:Image(icon,foreground.R+foreground.G+foreground.B>1.5f))):null;
            if(button.Image!=image)button.Image=image;state.AppliedImage=image;
            bool onlyIcon=image!=null&&(p.TextMode=="none"||symbolic);
            if(onlyIcon)label="";
            else if(p.TextMode=="none")label=p.EssentialTextMode=="full"?full:Short(full);
            // Existing compact symbol actions stay single glyphs when icons
            // are enabled, and gain actual localized words when icons are off.
            if(button.ControlObject is System.Windows.FrameworkElement native)
            {
                native.HorizontalAlignment=onlyIcon?System.Windows.HorizontalAlignment.Left:state.Alignment;
                System.Windows.Automation.AutomationProperties.SetName(native,full);
            }
            int width=onlyIcon?28:state.Width;
            if(!onlyIcon&&width>0&&(label.Length>3||(image!=null&&label.Length>0)))width=-1;
            if(PreferredWidth(button)!=width)button.Width=width;
        }
        else if(p.TextMode=="none")label=p.EssentialTextMode=="full"?full:Short(full);
        string? tip=label!=full||p.TextMode!="full"?full+(string.IsNullOrWhiteSpace(hintSource)||hintSource==full?"":"\n"+WorkspaceAppearance.Text(hintSource)):hintSource==null?null:WorkspaceAppearance.Text(hintSource);
        if(c.ToolTip!=tip)c.ToolTip=tip;
        return label;
    }
    internal static void Layout(Control c,PluginPreferences p)
    {
        if(c.Tag as string=="presentation-pair"&&c is TableLayout pair)
            foreach(var row in pair.Rows)foreach(var cell in row.Cells)cell.ScaleWidth=p.TextMode!="none"||cell.Control is not Button b||!string.IsNullOrEmpty(b.Text);
    }
}
