namespace RhinoSceneFlow.Plugin;
internal sealed class SeasonalScope:IDisposable
{
    private readonly string? old=PlantService.SeasonOverride;
    internal SeasonalScope(string season){RhinoSceneFlow.Core.Seasons.Validate(season);PlantService.SeasonOverride=season;}
    public void Dispose()=>PlantService.SeasonOverride=old;
}
