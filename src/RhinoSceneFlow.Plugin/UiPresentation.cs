using Eto.Forms;
using Eto.Drawing;
namespace RhinoSceneFlow.Plugin;

/// <summary>Single writer for native captions. Source state never comes from rendered text.
/// Weak subscriptions do not retain document tools. Repeated polling updates are no-ops.</summary>
internal static class UiPresentation
{
    private static readonly List<WeakReference<UiCaption>> captions=[];
    private static PluginPreferences? current;
    private static string? signature;
    private static bool started;
    internal static PluginPreferences Preferences=>current??=PluginPreferences.Load();
    internal static Color Foreground
    {
        get { var p=Preferences;var c=p.Theme=="rhino"?Rhino.ApplicationSettings.AppearanceSettings.GetPaintColor(Rhino.ApplicationSettings.PaintColor.TextEnabled):p.Theme=="dark"?System.Drawing.Color.FromArgb(235,239,235):System.Drawing.Color.FromArgb(30,36,30);return Color.FromArgb(c.R,c.G,c.B); }
    }
    internal static void Register(UiCaption caption)
    {
        if(captions.Count%128==0)captions.RemoveAll(w=>!w.TryGetTarget(out _));
        captions.Add(new(caption));
    }
    internal static string Text(string source,bool user=false)
    {
        if(user)return source;
        var p=Preferences;string text=NativeText.Translate(source,p.ResolvedLanguage);
        return p.TextMode=="short"||(p.TextMode=="none"&&p.EssentialTextMode=="short")?InterfacePresentation.Short(text):text;
    }
    internal static void Refresh(PluginPreferences p)
    {
        string next=p.ResolvedLanguage+"|"+p.TextMode+"|"+p.ShowIcons+"|"+p.EssentialTextMode+"|"+p.Theme+"|"+ForegroundKey();
        current=p;if(signature==next)return;signature=next;
        foreach(var weak in captions.ToArray())if(weak.TryGetTarget(out var caption))caption.Render();
        captions.RemoveAll(w=>!w.TryGetTarget(out _));
    }
    private static string ForegroundKey()=>Rhino.ApplicationSettings.AppearanceSettings.GetPaintColor(Rhino.ApplicationSettings.PaintColor.TextEnabled).ToArgb().ToString();
    internal static void Start(){started=true;Refresh(PluginPreferences.Load());Rhino.RhinoApp.AppSettingsChanged+=SettingsChanged;}
    private static void SettingsChanged(object? sender,EventArgs e)
    {
        if(!started)return;
        Rhino.RhinoApp.InvokeOnUiThread((Action)(()=>{if(started)SceneFlowWorkspace.RefreshAppearance(PluginPreferences.Load());}));
    }
    internal static void Stop(){started=false;Rhino.RhinoApp.AppSettingsChanged-=SettingsChanged;captions.Clear();current=null;signature=null;}
}

internal sealed class UiCaption
{
    private readonly Control? control;
    private readonly Func<string?> read;
    private readonly Action<string> write;
    private readonly Func<bool> user;
    private readonly Func<string,string>? localize;
    private readonly Action<string?>? writeHint;
    private readonly Func<string?>? readHint;
    private string? hintSource;
    private string source="";
    private readonly List<string> additions=[];
    internal bool Rendering{get;private set;}
    internal bool Loaded;
    internal UiCaption(Control? control,Func<string?> read,Action<string> write,Func<bool>? user=null,Func<string?>? readHint=null,Action<string?>? writeHint=null,Func<string,string>? localize=null)
    {
        this.control=control;this.read=read;this.write=write;this.user=user??(()=>control?.Tag as string=="user-content");
        this.readHint=readHint;this.writeHint=writeHint;this.localize=localize;
        UiPresentation.Register(this);
        if(control!=null)control.Load+=(_,_)=>{Loaded=true;Render();};
    }
    internal void Set(string? value){if(Rendering)return;value??="";if(source==value&&additions.Count==0)return;source=value;additions.Clear();Render();}
    internal void SetHint(string? value){if(Rendering||hintSource==value)return;hintSource=value;Render();}
    internal void Append(string value){additions.Add(value);Render();}
    private string FullSource()
    {
        string Localize(string value)
        {
            if(user())return value;
            int offset=0;while(offset<value.Length&&value[offset] is '\r' or '\n')offset++;
            return value[..offset]+(localize?.Invoke(value[offset..])??NativeText.Translate(value[offset..],UiPresentation.Preferences.ResolvedLanguage));
        }
        return Localize(source)+string.Concat(additions.Select(Localize));
    }
    internal void Render()
    {
        if(Rendering||control?.IsDisposed==true)return;
        Rendering=true;
        try
        {
            string full=FullSource();
            string text=localize!=null?full:UiPresentation.Text(full,user());
            if(control!=null&&Loaded&&!user())text=InterfacePresentation.Caption(control,full,UiPresentation.Preferences,UiPresentation.Foreground,hintSource);
            else if(writeHint!=null)
            {
                string? hint=hintSource==null?null:NativeText.Translate(hintSource,UiPresentation.Preferences.ResolvedLanguage);
                if(readHint?.Invoke()!=hint)writeHint(hint);
            }
            if((read()??"")!=text)write(text);
            if(control is Button button&&Loaded)InterfacePresentation.NormalizeIconVisual(button);
        }
        finally{Rendering=false;}
    }
}

internal class UiLabel:Label
{
    private UiCaption? caption;
    private UiCaption Caption=>caption??=new(this,()=>base.Text,v=>base.Text=v,readHint:()=>base.ToolTip,writeHint:v=>base.ToolTip=v);
    public override string Text{get=>base.Text;set=>Caption.Set(value);}
    [System.Diagnostics.CodeAnalysis.AllowNull] public new object Tag{get=>base.Tag;set{base.Tag=value;caption?.Render();}}
    internal void Append(string text)=>Caption.Append(text);
    [System.Diagnostics.CodeAnalysis.AllowNull] public override string ToolTip{get=>base.ToolTip;set{if(Caption.Rendering)base.ToolTip=value;else Caption.SetHint(value);}}
}
internal class UiButton:Button
{
    private UiCaption? caption;
    private UiCaption Caption=>caption??=new(this,()=>base.Text,v=>base.Text=v,readHint:()=>base.ToolTip,writeHint:v=>base.ToolTip=v);
    public override string Text{get=>base.Text;set=>Caption.Set(value);}
    public new Image? Image{get=>base.Image;set{base.Image=value;if(caption?.Rendering!=true)caption?.Render();}}
    [System.Diagnostics.CodeAnalysis.AllowNull] public override string ToolTip{get=>base.ToolTip;set{if(Caption.Rendering)base.ToolTip=value;else Caption.SetHint(value);}}
    [System.Diagnostics.CodeAnalysis.AllowNull] public new object Tag{get=>base.Tag;set{base.Tag=value;caption?.Render();}}
}
internal class UiCheckBox:CheckBox
{
    private UiCaption? caption;
    private UiCaption Caption=>caption??=new(this,()=>base.Text,v=>base.Text=v,readHint:()=>base.ToolTip,writeHint:v=>base.ToolTip=v);
    public override string Text{get=>base.Text;set=>Caption.Set(value);}
    [System.Diagnostics.CodeAnalysis.AllowNull] public new object Tag{get=>base.Tag;set{base.Tag=value;caption?.Render();}}
    [System.Diagnostics.CodeAnalysis.AllowNull] public override string ToolTip{get=>base.ToolTip;set{if(Caption.Rendering)base.ToolTip=value;else Caption.SetHint(value);}}
}
internal class UiListItem:ListItem
{
    private UiCaption? caption;
    internal bool? IsUserContent{get;set;}
    internal Func<string,string>? Localize{get;set;}
    private bool User=>Localize==null&&(IsUserContent??(!string.IsNullOrEmpty(Key)&&(Guid.TryParse(Key,out _)||System.IO.Path.IsPathFullyQualified(Key)||Key==source)));
    private string source="";
    private UiCaption Caption=>caption??=new(null,()=>base.Text,v=>base.Text=v,()=>User,localize:Localize);
    public new string Text{get=>base.Text;set{source=value;Caption.Set(value);}}
}
internal class UiButtonMenuItem:ButtonMenuItem
{
    private UiCaption? caption;
    private UiCaption Caption=>caption??=new(null,()=>base.Text,v=>base.Text=v);
    public new string Text{get=>base.Text;set=>Caption.Set(value);}
}
internal class UiGroupBox:GroupBox
{
    private UiCaption? caption;
    private UiCaption Caption=>caption??=new(this,()=>base.Text,v=>base.Text=v,readHint:()=>base.ToolTip,writeHint:v=>base.ToolTip=v);
    public new string Text{get=>base.Text;set=>Caption.Set(value);}
    [System.Diagnostics.CodeAnalysis.AllowNull] public override string ToolTip{get=>base.ToolTip;set{if(Caption.Rendering)base.ToolTip=value;else Caption.SetHint(value);}}
}
internal class UiExpander:Expander
{
    public new object Header{get=>base.Header;set=>base.Header=value is string text?new UiLabel{Text=text}:value as Control;}
}
internal class UiGridColumn:GridColumn
{
    private UiCaption? caption;
    private UiCaption Caption=>caption??=new(null,()=>base.HeaderText,v=>base.HeaderText=v);
    public new string HeaderText{get=>base.HeaderText;set=>Caption.Set(value);}
}
internal class UiTextBox:TextBox
{
    private UiCaption? placeholder;
    private UiCaption Placeholder=>placeholder??=new(this,()=>base.PlaceholderText,v=>base.PlaceholderText=v,user:()=>false,readHint:()=>base.ToolTip,writeHint:v=>base.ToolTip=v);
    public new string PlaceholderText{get=>base.PlaceholderText;set=>Placeholder.Set(value);}
    [System.Diagnostics.CodeAnalysis.AllowNull] public override string ToolTip{get=>base.ToolTip;set{if(Placeholder.Rendering)base.ToolTip=value;else Placeholder.SetHint(value);}}
}

