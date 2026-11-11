using Eto.Forms;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

/// <summary>One global draft, independent of document changes. Explicit save keeps invalid
/// angle combinations from partially changing live billboards.</summary>
internal sealed class SettingsTool:Panel
{
    private readonly DropDown language=new(){Width=100},theme=new(){Width=100},mode=new(){Width=100},climateMode=new(){Width=100};
    private readonly DropDown textMode=new(){Width=100},icons=new(){Width=100},essentialText=new(){Width=100};
    private readonly UiTextBox climate=new();
    private readonly Panel locationHost=new();
    private readonly UiCheckBox four=new();
    private readonly NumericStepper angle=Ui.Number(10,80),plan=Ui.Number(20,90),transition=Ui.Number(1,15),ratio=Ui.Number(0,2,2);
    private readonly UiLabel feedback=ToolUi.Note("");
    private readonly UiButton save=new();
    private bool syncing,dirty;
    private string T(string zh,string en)=>PluginPreferences.Load().ResolvedLanguage=="en"?en:zh;
    internal SettingsTool()
    {
        void Choices(DropDown d,params (string Key,string Zh,string En)[] items){foreach(var i in items)d.Items.Add(new UiListItem{Key=i.Key,Text=T(i.Zh,i.En)});}
        Choices(language,("auto","跟随 Rhino","Follow Rhino"),("zh","中文","中文"),("en","English","English"));
        Choices(theme,("rhino","跟随 Rhino","Follow Rhino"),("light","浅色","Light"),("dark","深色","Dark"));
        Choices(mode,("auto","自动切换","Automatic"),("z","立面 · 沿 Z 轴","Elevation · Z axis"),("free","立面 · 朝向相机","Elevation · Face camera"),("plan","平面图","Plan"));
        var general=Ui.Layout();Field(general,T("显示语言","Display language"),language);Field(general,T("界面主题","Interface theme"),theme);
        general.AddRow(ToolUi.Note(T("影响 Rhino 侧栏和素材对话；Web 工作台有独立的语言设置。","Applies to Rhino panels and asset chat. Web Studio has its own language setting.")));
        Choices(textMode,("full","全称","Full"),("short","缩写","Abbreviated"),("none","无","None"));
        Choices(icons,("show","显示","Show"),("none","无","None"));
        Choices(essentialText,("short","缩写","Abbreviated"),("full","全称","Full"));
        Field(general,T("界面文字","Interface text"),textMode);
        Field(general,T("界面图标","Interface icons"),icons);
        Field(general,T("必要文字（无文字模式）","Essential text (icon mode)"),essentialText);
        general.AddRow(ToolUi.Note(T("至少保留文字或图标。素材名、输入值和状态仍显示；悬停查看全称。设置影响 Rhino 工具页，不改写素材或网页内容。","Keep text or icons visible. Names, values and status remain readable; hover for full labels. Applies to Rhino tools, not asset data or web content.")));
        general.AddRow(ToolUi.Note(T("界面选项立即生效；其他设置使用下方保存按钮。","Interface options apply immediately. Use Save for other settings.")));
        general.AddRow(Ui.Button(T("恢复界面默认","Reset interface defaults"),()=>{syncing=true;try{language.SelectedKey="auto";theme.SelectedKey="rhino";textMode.SelectedKey="full";icons.SelectedKey="show";essentialText.SelectedKey="short";}finally{syncing=false;}ApplyAppearance(textMode);}));
        var generation=Ui.Layout();
        Choices(climateMode,("species","按物种适生气候（默认）","Species' native climate (default)"),("project","指定项目地区","Specify project location"));
        Field(generation,T("季节气候依据","Seasonal climate context"),climateMode);
        climate.PlaceholderText=T("例如：迈阿密，佛罗里达","e.g. Miami, Florida");
        var location=Ui.Layout();Field(location,T("项目地区","Project location"),climate);locationHost.Content=location;generation.AddRow(locationHost);
        generation.AddRow(ToolUi.Note(T("用于后续季节版本，不会自动重新生成已有图片。","Used for new seasonal variants; existing images stay unchanged.")));
        four.Text=T("默认生成四季版本","Generate all seasons by default");generation.AddRow(four);
        generation.AddRow(ToolUi.Note(T("默认生成夏季；植物同时补齐立面和平面。缺失版本回退夏季。","Summer is the default. Plants get elevation and plan images. Missing variants fall back to summer.")));
        generation.AddRow(Ui.Button(T("恢复生成默认","Reset generation defaults"),()=>{climateMode.SelectedKey="species";climate.Text="";four.Checked=false;}));
        var plants=Ui.Layout();Field(plants,T("朝向模式","Facing mode"),mode);
        plants.AddRow(ToolUi.Note(T("按镜头俯角切换：水平 0°，正俯视 90°。","Switches by camera elevation: horizontal 0°, top-down 90°.")));
        Field(plants,T("自由朝向中心角 · °","Free-facing centre · °"),angle);Field(plants,T("过渡半宽 · °","Transition half-width · °"),transition);Field(plants,T("平面图起始角 · °","Plan starts at · °"),plan);
        Field(plants,T("平面抬升比例 · 实际树高 × 比例","Plan lift · actual tree height × ratio"),ratio);
        plants.AddRow(ToolUi.Note(T("自动：低角度沿 Z 轴，过渡后朝向相机，高俯视使用平面。平面缺失时暂用立面。","Auto: Z axis at low angles, face camera after transition, plan at high angles. Missing plans use elevation temporarily.")));
        plants.AddRow(Ui.Button(T("恢复植物显示默认","Reset plant display defaults"),()=>LoadPlants(new())));
        var content=Ui.Layout();content.Padding=new(0,0,5,8);
        content.AddRow(ToolUi.Heading(T("设置","Settings")));
        content.AddRow(ToolUi.Note(T("全局设置 · 所有 Rhino 文件共用","Global settings · shared by all Rhino documents")));
        content.AddRow(Section(T("界面","Interface"),general,true));content.AddRow(Section(T("素材生成","Asset generation"),generation,false));content.AddRow(Section(T("植物显示","Plant display"),plants,true));content.AddRow(null);
        save.Text=T("保存设置","Save settings");save.Click+=(_,_)=>SaveDraft();
        var discard=Ui.Button(T("还原未保存修改","Discard unsaved changes"),()=>LoadDraft());
        var footer=Ui.Layout();footer.AddRow(feedback);footer.AddRow(save);footer.AddRow(discard);
        var scroll=ToolUi.VerticalScroll(content);
        var root=Ui.Layout();root.Add(scroll,true,true);root.AddRow(footer);Content=root;
        foreach(var d in new[]{language,theme,textMode,icons,essentialText})d.SelectedValueChanged+=(_,_)=>ApplyAppearance(d);
        foreach(var d in new[]{mode,climateMode})d.SelectedValueChanged+=(_,_)=>Changed();
        climate.TextChanged+=(_,_)=>Changed();four.CheckedChanged+=(_,_)=>Changed();
        foreach(var n in new[]{angle,plan,transition,ratio})n.ValueChanged+=(_,_)=>Changed();
        LoadDraft();
    }
    internal void SyncAppearance(PluginPreferences p)
    {
        bool previous=syncing;syncing=true;
        try{language.SelectedKey=p.Language;theme.SelectedKey=p.Theme;textMode.SelectedKey=p.TextMode;icons.SelectedKey=p.ShowIcons?"show":"none";essentialText.SelectedKey=p.EssentialTextMode;UpdateMode();}
        finally{syncing=previous;}
    }
    private void ApplyAppearance(DropDown changed)
    {
        if(syncing)return;syncing=true;
        try
        {
            if(textMode.SelectedKey=="none"&&icons.SelectedKey=="none")
            {
                if(changed==icons)textMode.SelectedKey=essentialText.SelectedKey??"short";
                else icons.SelectedKey="show";
            }
            var p=PluginPreferences.Load();p.Language=language.SelectedKey!;p.Theme=theme.SelectedKey!;
            p.TextMode=textMode.SelectedKey!;p.ShowIcons=icons.SelectedKey=="show";p.EssentialTextMode=essentialText.SelectedKey!;
            PluginPreferences.Save(p);UpdateMode();
            feedback.Text=dirty?T("有未保存修改","Unsaved changes"):T("设置已立即保存。","Appearance saved and applied immediately.");
        }
        catch(Exception e){feedback.Text=T("未保存：","Not saved: ")+e.Message;SyncAppearance(PluginPreferences.Load());}
        finally{syncing=false;}
    }
    private static void Field(DynamicLayout layout,string label,Control control){layout.AddRow(ToolUi.Note(label));layout.AddRow(control);}
    private static UiGroupBox Section(string name,Control content,bool expanded)=>new(){Content=new Panel{Padding=new(8),Content=new UiExpander{Header=name,Expanded=expanded,Content=content}}};
    private void LoadPlants(BillboardSettings b){mode.SelectedKey=b.Mode;angle.Value=b.Angle;plan.Value=b.PlanAngle;transition.Value=b.Transition;ratio.Value=b.PlanHeightRatio;}
    private void LoadDraft()
    {
        syncing=true;try{var p=PluginPreferences.Load();language.SelectedKey=p.Language;theme.SelectedKey=p.Theme;textMode.SelectedKey=p.TextMode;icons.SelectedKey=p.ShowIcons?"show":"none";essentialText.SelectedKey=p.EssentialTextMode;climateMode.SelectedKey=p.ClimateMode;climate.Text=p.Climate;four.Checked=p.GenerateFourSeasons;LoadPlants(PlantService.Settings);dirty=false;save.Enabled=false;feedback.Text=T("设置已保存到本机。","Settings saved on this computer.");UpdateMode();}finally{syncing=false;}
    }
    private void UpdateMode(){essentialText.Enabled=textMode.SelectedKey=="none";bool auto=mode.SelectedKey=="auto";angle.Enabled=transition.Enabled=plan.Enabled=auto;locationHost.Visible=climateMode.SelectedKey=="project";}
    private void Changed(){if(syncing)return;dirty=true;save.Enabled=true;feedback.Text=T("有未保存修改","Unsaved changes");UpdateMode();}
    internal void SaveDraft()
    {
        try
        {
            var b=new BillboardSettings{Mode=mode.SelectedKey!,Angle=angle.Value,PlanAngle=plan.Value,Transition=transition.Value,PlanHeightRatio=ratio.Value};b.Validate();
            if(climateMode.SelectedKey=="project"&&string.IsNullOrWhiteSpace(climate.Text))throw new ArgumentException(T("请填写项目地区。","Enter a project location."));
            var p=PluginPreferences.Load();p.Language=language.SelectedKey!;p.Theme=theme.SelectedKey!;p.TextMode=textMode.SelectedKey!;p.ShowIcons=icons.SelectedKey=="show";p.EssentialTextMode=essentialText.SelectedKey!;p.ClimateMode=climateMode.SelectedKey!;p.Climate=climate.Text;p.GenerateFourSeasons=four.Checked==true;
            PluginPreferences.Save(p);PlantService.Settings=b;dirty=false;save.Enabled=false;feedback.Text=T("已保存 · 当前场景已刷新","Saved · current scene refreshed");
        }
        catch(Exception e){feedback.Text=T("未保存：","Not saved: ")+e.Message;}
    }
    internal object State()=>new{dirty,language=language.SelectedKey,theme=theme.SelectedKey,textMode=textMode.SelectedKey,showIcons=icons.SelectedKey=="show",essentialTextMode=essentialText.SelectedKey,mode=mode.SelectedKey,climateMode=climateMode.SelectedKey,locationVisible=locationHost.Visible,feedback=feedback.Text};
}
