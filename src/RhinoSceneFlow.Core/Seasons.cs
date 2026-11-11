namespace RhinoSceneFlow.Core;

public static class Seasons
{
    public static readonly string[] All=["spring","summer","autumn","winter"];
    public static string Name(string season)=>season switch{"spring"=>"春","summer"=>"夏","autumn"=>"秋","winter"=>"冬",_=>throw new ArgumentException("Invalid season.")};
    public static void Validate(string season){if(!All.Contains(season))throw new ArgumentException("Season: spring | summer | autumn | winter.");}
    public static string Effective(MaterialAsset a,string season){Validate(season);return a.Seasonal.FollowSeason?season:a.Seasonal.FixedSeason;}
    public static string Slot(MaterialAsset a,string season,bool plan=false)
    {
        season=Effective(a,season);if(a.Seasonal.Variants.TryGetValue(season,out var v)&&(plan?v.Plan:v.Elevation) is string slot)return slot;
        return a.Seasonal.Variants.TryGetValue("summer",out var summer)?(plan?summer.Plan:summer.Elevation)??"baseColor":"baseColor";
    }
    public static bool Has(MaterialAsset a,string season,bool plan=false)=>a.Seasonal.Variants.TryGetValue(season,out var v)&&(plan?v.Plan:v.Elevation) is string slot&&a.Maps.ContainsKey(slot);
}
public sealed class SeasonalAppearance
{
    public bool FollowSeason{get;set;}=true;
    public string FixedSeason{get;set;}="summer";
    public string Climate{get;set;}="依照已核实物种的适生气候";
    public Dictionary<string,SeasonVariant> Variants{get;set;}=[];
    public void Validate(MaterialAsset a)
    {
        Seasons.Validate(FixedSeason);
        if(Climate.Length>300||Variants.Count>4)throw new ArgumentException("Invalid seasonal metadata.");
        foreach(var (season,v) in Variants){Seasons.Validate(season);if(v.Elevation!=null&&!a.Maps.ContainsKey(v.Elevation)||v.Plan!=null&&!a.Maps.ContainsKey(v.Plan)||!double.IsFinite(v.CrownWidthMeters)||v.CrownWidthMeters<=0||v.CrownWidthMeters>1000||v.ElevationWidthMeters.HasValue&&(!double.IsFinite(v.ElevationWidthMeters.Value)||v.ElevationWidthMeters<=0)||v.AnchorU.HasValue&&(!double.IsFinite(v.AnchorU.Value)||v.AnchorU<0||v.AnchorU>1))throw new ArgumentException("Invalid seasonal image reference/dimensions.");}
    }
}
public sealed class SeasonVariant
{
    public string? Elevation{get;set;}
    public string? Plan{get;set;}
    public double CrownWidthMeters{get;set;}=3;
    public double? ElevationWidthMeters{get;set;}
    public double? AnchorU{get;set;}
}
