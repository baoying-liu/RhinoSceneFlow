using System.Net;
using System.Net.Http;
using System.Text.Json;

namespace RhinoSceneFlow.Core;

public sealed record ReleaseOffer(string Version, string Page, string Notes, string? Installer, string? Sha256, long Bytes);

/// <summary>Public releases only. No GitHub credentials, arbitrary feeds or executable redirects in metadata.</summary>
public static class ReleaseFeed
{
    public const string Repository = "baoying-liu/RhinoSceneFlow";
    public const string ReleasesPage = "https://github.com/" + Repository + "/releases";
    public static bool TryVersion(string? text, out Version version)
    {
        version = new Version(0, 0, 0);
        return text is not null && System.Text.RegularExpressions.Regex.IsMatch(text, @"^[vV]?\d+\.\d+\.\d+$") && Version.TryParse(text.TrimStart('v', 'V'), out version!);
    }
    public static bool IsReleaseUrl(string? value)
    {
        return Uri.TryCreate(value, UriKind.Absolute, out var uri) && uri.Scheme == "https" &&
            uri.Host == "github.com" && uri.IsDefaultPort && uri.UserInfo.Length == 0 && uri.Query.Length == 0 && uri.Fragment.Length == 0 &&
            uri.AbsolutePath.StartsWith("/" + Repository + "/releases/", StringComparison.Ordinal);
    }
    public static ReleaseOffer? Parse(string json, Version current)
    {
        using var document = JsonDocument.Parse(json);
        var r = document.RootElement;
        if (r.GetProperty("draft").GetBoolean() || r.GetProperty("prerelease").GetBoolean()) return null;
        if (!TryVersion(r.GetProperty("tag_name").GetString(), out var version) || version <= current) return null;
        string page = r.GetProperty("html_url").GetString()!;
        if (!IsReleaseUrl(page)) throw new InvalidDataException("Unexpected release origin.");
        string expected = $"SceneFlow-Setup-{version.ToString(3)}-win-x64.exe";
        var assets = r.GetProperty("assets").EnumerateArray().Where(a => a.GetProperty("name").GetString() == expected).ToArray();
        if (assets.Length > 1) throw new InvalidDataException("Ambiguous installer assets.");
        string? url = null, hash = null; long bytes = 0;
        if (assets.Length == 1)
        {
            var a = assets[0]; url = a.GetProperty("browser_download_url").GetString();
            if (!IsReleaseUrl(url)) throw new InvalidDataException("Unexpected installer origin.");
            bytes = a.GetProperty("size").GetInt64();
            if (bytes <= 0 || bytes > 2L * 1024 * 1024 * 1024) throw new InvalidDataException("Unexpected installer size.");
            if (a.TryGetProperty("digest", out var digest) && digest.ValueKind == JsonValueKind.String)
            {
                var value = digest.GetString()!;
                if (value.StartsWith("sha256:", StringComparison.Ordinal) && value.Length == 71 && value[7..].All(Uri.IsHexDigit)) hash = value[7..];
            }
        }
        return new(version.ToString(3), page, r.TryGetProperty("body", out var body) ? body.GetString() ?? "" : "", url, hash, bytes);
    }
    public static async Task<ReleaseOffer?> CheckAsync(Version current, CancellationToken token)
    {
        using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(20), MaxResponseContentBufferSize = 4 * 1024 * 1024 };
        http.DefaultRequestHeaders.UserAgent.ParseAdd("RhinoSceneFlow/" + current.ToString(3));
        http.DefaultRequestHeaders.Accept.ParseAdd("application/vnd.github+json");
        using var response = await http.GetAsync("https://api.github.com/repos/" + Repository + "/releases/latest", token);
        // A private/unpublished repository is not an authentication failure for the user's AI account.
        if (response.StatusCode == HttpStatusCode.NotFound) throw new InvalidOperationException("release_not_public");
        if (response.StatusCode is HttpStatusCode.Forbidden or HttpStatusCode.TooManyRequests) throw new InvalidOperationException("release_rate_limit");
        response.EnsureSuccessStatusCode();
        return Parse(await response.Content.ReadAsStringAsync(token), current);
    }
}
