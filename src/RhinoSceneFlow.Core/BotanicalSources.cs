using System.Net;
using System.Text;
using System.Text.RegularExpressions;

namespace RhinoSceneFlow.Core;

public sealed record BotanicalSourceCheck(string Url,string FinalUrl,string Outcome,int? Status=null);
public static class BotanicalSources
{
    public static bool Allowed(string value)=>Uri.TryCreate(value,UriKind.Absolute,out var u)&&u.Scheme=="https"&&new[]{"kew.org","worldfloraonline.org","missouribotanicalgarden.org","mobot.org","ncsu.edu","usda.gov","gbif.org","rhs.org.uk","nparks.gov.sg","ifas.ufl.edu"}.Any(d=>u.Host.Equals(d,StringComparison.OrdinalIgnoreCase)||u.Host.EndsWith("."+d,StringComparison.OrdinalIgnoreCase));
    public static bool Matches(string html,string scientificName,string family)
    {
        string text=WebUtility.HtmlDecode(Regex.Replace(html,"<[^>]+>"," "));
        text=Regex.Replace(text,@"\s+"," ");
        bool Contains(string value,string term)=>!string.IsNullOrWhiteSpace(term)&&Regex.IsMatch(Regex.Replace(value,@"\s+"," "),@"(?<![\p{L}\p{N}])"+Regex.Escape(term.Trim())+@"(?![\p{L}\p{N}])",RegexOptions.IgnoreCase|RegexOptions.CultureInvariant);
        // A related-species mention in the body of another taxon's page is not
        // an identity source. Require a species heading/title or explicit label.
        bool identified=Regex.Matches(html,@"<(title|h[1-3])\b[^>]*>(.*?)</\1>",RegexOptions.IgnoreCase|RegexOptions.Singleline)
            .Any(m=>Contains(WebUtility.HtmlDecode(Regex.Replace(m.Groups[2].Value,"<[^>]+>"," ")),scientificName));
        if(!identified&&!string.IsNullOrWhiteSpace(scientificName))identified=Regex.IsMatch(text,@"\bScientific\s+name\s*:?\s*"+Regex.Escape(scientificName.Trim())+@"(?![\p{L}\p{N}])",RegexOptions.IgnoreCase|RegexOptions.CultureInvariant);
        return identified&&Contains(text,scientificName)&&Contains(text,family);
    }
    public static async Task<BotanicalSourceCheck[]> CheckAsync(HttpClient http,IEnumerable<string> candidates,string scientificName,string family,CancellationToken cancel)
    {
        var urls=candidates.Where(Allowed).Distinct(StringComparer.OrdinalIgnoreCase).OrderBy(s=>Uri.TryCreate(s,UriKind.Absolute,out var u)&&u.AbsolutePath.EndsWith(".pdf",StringComparison.OrdinalIgnoreCase)?1:0).Take(12).ToArray();
        using var gate=new SemaphoreSlim(4);
        return await Task.WhenAll(urls.Select(async url=>
        {
            await gate.WaitAsync(cancel);
            try
            {
                if(new Uri(url).AbsolutePath.EndsWith(".pdf",StringComparison.OrdinalIgnoreCase))return new BotanicalSourceCheck(url,url,"unsupported_pdf");
                using var response=await http.GetAsync(url,HttpCompletionOption.ResponseHeadersRead,cancel);
                string final=response.RequestMessage?.RequestUri?.AbsoluteUri??url;
                if(!Allowed(final))return new BotanicalSourceCheck(url,final,"untrusted_redirect",(int)response.StatusCode);
                if(!response.IsSuccessStatusCode)return new BotanicalSourceCheck(url,final,"http_error",(int)response.StatusCode);
                string media=response.Content.Headers.ContentType?.MediaType??"";
                if(media.Length>0&&!media.Contains("html",StringComparison.OrdinalIgnoreCase)&&!media.StartsWith("text/",StringComparison.OrdinalIgnoreCase))return new BotanicalSourceCheck(url,final,"unsupported_content",(int)response.StatusCode);
                using var body=await response.Content.ReadAsStreamAsync(cancel);using var bytes=new MemoryStream();byte[] buffer=new byte[16384];int count;
                while((count=await body.ReadAsync(buffer,cancel))>0){if(bytes.Length+count>6_000_000)return new BotanicalSourceCheck(url,final,"too_large");bytes.Write(buffer,0,count);}
                bool matched=Matches(Encoding.UTF8.GetString(bytes.ToArray()),scientificName,family);
                return new BotanicalSourceCheck(url,final,matched?"verified":"identity_not_found",(int)response.StatusCode);
            }
            catch(Exception e) when(e is HttpRequestException or TaskCanceledException)
            {cancel.ThrowIfCancellationRequested();return new BotanicalSourceCheck(url,url,e is TaskCanceledException?"timeout":"network_error");}
            finally{gate.Release();}
        }));
    }
}
