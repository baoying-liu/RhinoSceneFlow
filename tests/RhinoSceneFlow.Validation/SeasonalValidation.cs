using RhinoSceneFlow.Core;
internal static class SeasonalValidation
{
    public static void Run(string output)
    {
        string folder=Path.Combine(Path.GetFullPath(output),"seasons-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(folder);var library=new MaterialLibrary(Path.Combine(folder,"library"));
        string image=Path.Combine(folder,"image.png");File.WriteAllBytes(image,[1,2,3,4]);
        var asset=library.Import(new MaterialAsset{Name="Season specimen"},new Dictionary<string,string>{{"baseColor",image}});
        void Check(bool value,string message){if(!value)throw new Exception(message);}
        Check(Seasons.Slot(asset,"winter")=="baseColor"&&asset.Seasonal.FollowSeason,"Legacy/missing fallback.");
        int revision=asset.Revision;asset=library.AddSeason(asset.Id,revision,"summer",true,image,crownWidthMeters:5);
        try{library.AddSeason(asset.Id,revision,"winter",false,image);throw new Exception("Stale commit accepted.");}catch(InvalidOperationException){}
        foreach(string s in new[]{"spring","autumn"}){asset=library.AddSeason(asset.Id,asset.Revision,s,false,null,"baseColor");asset=library.AddSeason(asset.Id,asset.Revision,s,true,null,"summer_plan",5);}
        asset=library.AddSeason(asset.Id,asset.Revision,"winter",false,image,elevationWidthMeters:1.75,anchorU:.3);asset=library.AddSeason(asset.Id,asset.Revision,"winter",true,image,crownWidthMeters:5);
        asset=library.AddSeason(asset.Id,asset.Revision,"autumn",false,null,"winter_elevation");Check(asset.Seasonal.Variants["autumn"].ElevationWidthMeters==1.75&&asset.Seasonal.Variants["autumn"].AnchorU==.3,"Aliased image geometry must follow its source slot.");
        Check(library.List().Length==1&&asset.Maps.Count==4,"Variants must not create library rows or duplicate aliases.");
        asset.Seasonal.FollowSeason=false;asset.Seasonal.FixedSeason="winter";asset=library.Update(asset);Check(Seasons.Slot(asset,"summer")=="winter_elevation","Fixed season respected.");
        string package=Path.Combine(folder,"plant.zip");library.ExportPackage(asset.Id,package);var imported=new MaterialLibrary(Path.Combine(folder,"other")).ImportPackage(package);
        Check(imported.Seasonal.Variants.Count==4&&imported.Maps.Count==4,"Season package roundtrip.");
        var settings=new BillboardSettings();settings.Validate();var camera=new CameraProjection(new(0,0,10),new(1,0,0),new(0,1,0),new(0,0,1),-1,1,-1,1,1,100,true);
        var plant=new PlantBillboard("p","s","p",new(0,0,2),3,3,.5,.5,false,new(1,1,[1,2,3,255])){IsPlan=true};var axes=plant.Axes(camera,settings);
        Check(axes.Right.Z==0&&axes.Up.Z==0&&PlantBillboard.Elevation(camera,plant.Anchor)==90,"Plan is horizontal and angle definition is consistent.");
        settings.PlanAngle=60;try{settings.Validate();throw new Exception("Overlapping angle intervals accepted.");}catch(ArgumentException){}
        Console.WriteLine("PASS: seasonal aliases, missing/fixed fallback, one library identity, stale rejection, packaging and plan axes.");
    }
}
