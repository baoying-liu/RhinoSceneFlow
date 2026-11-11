using System.Text.Json;
using System.Text.RegularExpressions;
namespace RhinoSceneFlow.Plugin;

/// <summary>Full and short captions share one bilingual source. Rendered labels
/// never become the language source; user values are not passed through this catalog.</summary>
internal static class NativeText
{
    private sealed class Entry
    {
        public string Zh {get;set;}="";
        public string En {get;set;}="";
        public string ShortZh {get;set;}="";
        public string ShortEn {get;set;}="";
    }
    private sealed record Format(Entry Entry,Regex Zh,Regex En);
    private static readonly Dictionary<string,Entry> captions=new(StringComparer.Ordinal);
    private static readonly List<Format> formats=[];
    static NativeText()
    {
        foreach(var pair in WorkspaceAppearance.english)Add(new(){Zh=pair.Key,En=pair.Value});
        using var resource=typeof(NativeText).Assembly.GetManifestResourceStream("RhinoSceneFlow.Plugin.Resources.NativeText.json")??throw new InvalidOperationException("Native text catalog is missing.");
        foreach(var entry in JsonSerializer.Deserialize<Entry[]>(resource,new JsonSerializerOptions{PropertyNameCaseInsensitive=true})!)Add(entry);
        formats.Sort((a,b)=>b.Entry.Zh.Length.CompareTo(a.Entry.Zh.Length));
    }
    private static Regex Pattern(string template)
    {
        var pattern=new System.Text.StringBuilder("^");int offset=0;
        foreach(Match token in Regex.Matches(template,@"\{\d+\}"))
        {
            pattern.Append(Regex.Escape(template[offset..token.Index])).Append("([^\\r\\n]+?)");
            offset=token.Index+token.Length;
        }
        pattern.Append(Regex.Escape(template[offset..])).Append('$');
        return new(pattern.ToString(),RegexOptions.CultureInvariant);
    }
    private static void Add(Entry entry)
    {
        if(entry.Zh.Contains("{0}")){formats.Add(new(entry,Pattern(entry.Zh),Pattern(entry.En)));return;}
        captions[entry.Zh]=entry;captions[entry.En]=entry;
    }
    private static string Fill(string template,Match match)
    {
        for(int i=1;i<match.Groups.Count;i++)template=template.Replace("{"+(i-1)+"}",match.Groups[i].Value);
        return template;
    }
    internal static string Translate(string value,string language)
    {
        if(string.IsNullOrEmpty(value))return value??"";
        if(captions.TryGetValue(value,out var entry))return language=="en"?entry.En:entry.Zh;
        foreach(var format in formats)
        {
            var match=format.Zh.Match(value);if(!match.Success)match=format.En.Match(value);
            if(match.Success)
            {
                string template=language=="en"?format.Entry.En:format.Entry.Zh;
                if(format.Entry.Zh.StartsWith("去重复")||format.Entry.Zh.StartsWith("模式"))
                    return template.Replace("{0}",Translate(match.Groups[1].Value,language));
                return Fill(template,match);
            }
        }
        return value;
    }
    internal static string Canonical(string value)=>captions.TryGetValue(value,out var entry)?entry.Zh:value;
    internal static string? Short(string value)
    {
        if(captions.TryGetValue(value,out var entry))
        {
            string text=value==entry.En?entry.ShortEn:entry.ShortZh;
            return string.IsNullOrEmpty(text)?null:text;
        }
        foreach(var format in formats)
        {
            var match=format.En.Match(value);bool en=match.Success;if(!en)match=format.Zh.Match(value);
            string text=en?format.Entry.ShortEn:format.Entry.ShortZh;
            if(match.Success&&!string.IsNullOrEmpty(text))return Fill(text,match);
        }
        return null;
    }
}
