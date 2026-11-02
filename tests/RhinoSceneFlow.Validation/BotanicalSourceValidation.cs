using System.Net;
using RhinoSceneFlow.Core;
internal static class BotanicalSourceValidation
{
    private sealed class Sources:HttpMessageHandler
    {
        internal readonly List<string> Requested=[];
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request,CancellationToken cancel)
        {
            string url=request.RequestUri!.AbsoluteUri;lock(Requested)Requested.Add(url);
            var response=new HttpResponseMessage(url.Contains("kew.org")?HttpStatusCode.Forbidden:HttpStatusCode.OK){RequestMessage=request};
            response.Content=new StringContent(url.Contains("/name-only")?"Tamarindus indica":url.Contains("/family-only")?"Fabaceae":"<h1><i>Tamarindus</i>&nbsp;indica L.</h1><div>Family: Fabaceae (Leguminosae)</div>",System.Text.Encoding.UTF8,"text/html");
            if(url.Contains("/redirect"))response.RequestMessage=new(HttpMethod.Get,"https://evil.example/");
            return Task.FromResult(response);
        }
    }
    internal static void Run()
    {
        void Check(bool ok,string message){if(!ok)throw new Exception(message);}
        Check(BotanicalSources.Allowed("https://www.nparks.gov.sg/florafaunaweb/flora/3/1/3174"),"NParks source excluded.");
        Check(!BotanicalSources.Allowed("https://nparks.gov.sg.evil.example/a")&&!BotanicalSources.Allowed("http://www.nparks.gov.sg/a"),"Source trust boundary weakened.");
        Check(!BotanicalSources.Matches("Tamarindus indicax Fabaceae","Tamarindus indica","Fabaceae"),"Partial species token accepted.");
        Check(!BotanicalSources.Matches("<title>Dialium indum</title><h1>Dialium indum</h1><p>Fabaceae. Similar to Tamarindus indica.</p>","Tamarindus indica","Fabaceae"),"Related taxon mention accepted as a species page.");
        Check(BotanicalSources.Matches("<h1>Tamarind</h1><p>Scientific name: Tamarindus indica L. Family name: Fabaceae</p>","Tamarindus indica","Fabaceae"),"Explicit labelled scientific identity rejected.");
        using var handler=new Sources();using var http=new HttpClient(handler);
        var checks=BotanicalSources.CheckAsync(http,["https://powo.science.kew.org/taxon/test","https://www.usda.gov/file.pdf","https://www.nparks.gov.sg/florafaunaweb/flora/3/1/3174","https://www.nparks.gov.sg/name-only","https://www.nparks.gov.sg/family-only","https://www.nparks.gov.sg/redirect"],"Tamarindus indica","Fabaceae",CancellationToken.None).GetAwaiter().GetResult();
        Check(checks.Count(c=>c.Outcome=="verified")==1&&checks.Single(c=>c.Outcome=="verified").Url.Contains("/3174"),"Actual alternate page not verified or partial evidence accepted.");
        Check(checks.Any(c=>c.Outcome=="http_error")&&checks.Any(c=>c.Outcome=="unsupported_pdf")&&checks.Any(c=>c.Outcome=="untrusted_redirect"),"Source diagnostics incomplete.");
        Check(!handler.Requested.Any(u=>u.EndsWith(".pdf")),"PDF was treated as HTML.");
        using var cancelled=new CancellationTokenSource();cancelled.Cancel();bool stopped=false;
        try{BotanicalSources.CheckAsync(http,["https://www.nparks.gov.sg/a"],"Tamarindus indica","Fabaceae",cancelled.Token).GetAwaiter().GetResult();}catch(OperationCanceledException){stopped=true;}
        Check(stopped,"Botanical verification ignored cancellation.");
        Console.WriteLine("PASS: botanical alternate HTML sources, exact identity/family, domain/redirect boundary, PDF diagnostics and cancellation.");
    }
}
