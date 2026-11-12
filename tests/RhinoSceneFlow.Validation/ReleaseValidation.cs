using System.Text.Json;
using RhinoSceneFlow.Core;

internal static class ReleaseValidation
{
    internal static void Run()
    {
        static string Fixture(string tag = "v0.24.0", bool prerelease = false, string? url = null, string digest = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa") => JsonSerializer.Serialize(new {
            tag_name = tag, draft = false, prerelease, html_url = ReleaseFeed.ReleasesPage + "/tag/" + tag, body = "Release notes",
            assets = new[] { new { name = "SceneFlow-Setup-0.24.0-win-x64.exe", browser_download_url = url ?? ReleaseFeed.ReleasesPage + "/download/v0.24.0/SceneFlow-Setup-0.24.0-win-x64.exe", size = 1200L, digest } }
        });
        static void Require(bool value, string name) { if (!value) throw new Exception("Release validation: " + name); }
        var current = new Version(0, 23, 0);
        var offer = ReleaseFeed.Parse(Fixture(), current)!;
        Require(offer.Version == "0.24.0" && offer.Sha256?.Length == 64 && offer.Bytes == 1200, "exact named binary and GitHub digest");
        Require(ReleaseFeed.Parse(Fixture(prerelease: true), current) is null, "stable excludes previews");
        Require(ReleaseFeed.Parse(Fixture(tag: "v0.23.0"), current) is null, "same version");
        Require(ReleaseFeed.Parse(Fixture(tag: "v0.22.0"), current) is null, "no downgrade");
        Require(ReleaseFeed.Parse(Fixture(digest: "md5:not-a-sha256"), current)!.Sha256 is null, "missing hash is not installable");
        foreach (string invalid in new[] { "http://github.com/baoying-liu/RhinoSceneFlow/releases/a", "https://github.com.evil.test/baoying-liu/RhinoSceneFlow/releases/a", "https://user@github.com/baoying-liu/RhinoSceneFlow/releases/a", "https://github.com/other/repo/releases/a", "https://github.com/baoying-liu/RhinoSceneFlow/releases/a?redirect=evil", "https://github.com:444/baoying-liu/RhinoSceneFlow/releases/a" })
        {
            Require(!ReleaseFeed.IsReleaseUrl(invalid), "reject " + invalid);
            try { ReleaseFeed.Parse(Fixture(url: invalid), current); throw new Exception("Accepted foreign installer"); } catch (InvalidDataException) { }
        }
        foreach (var invalid in new[] { "vv0.24.0", "0.24", "0.24.0-beta", "0.24.0.1", "latest" }) Require(!ReleaseFeed.TryVersion(invalid, out _), "reject ambiguous version");
        Console.WriteLine("PASS: release versions, stable-only policy, exact installer names, digest gates and origin rejection.");
    }
}
