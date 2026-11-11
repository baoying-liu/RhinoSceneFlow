namespace RhinoSceneFlow.Core;

/// <summary>Language-independent preference values; never store a UI label as input.</summary>
public sealed record ClimateContext(string Mode,string Location)
{
    public const string SpeciesInstruction="Use the verified species' native climate; for natural materials use their documented environment. No project location is specified. Do not assume a city or region.";
    public string Instruction=>Mode=="species"?SpeciesInstruction:"Project location/climate: "+Location;
    public string Metadata=>Mode=="species"?SpeciesInstruction:Location;
    public static ClimateContext Resolve(string? mode,string? location)
    {
        location??="";
        if(mode is null)
        {
            bool legacyDefault=string.IsNullOrWhiteSpace(location)||location.Trim() is "依照已核实物种的适生气候" or "Use species' native climate" or "Use species’ native climate";
            mode=legacyDefault?"species":"project";
            if(legacyDefault)location="";
        }
        if(mode is not ("species" or "project")||location.Length>300)throw new ArgumentException("Invalid climate preference.");
        if(mode=="project"&&string.IsNullOrWhiteSpace(location))throw new ArgumentException("Enter a project location.");
        return new(mode,location);
    }
}
