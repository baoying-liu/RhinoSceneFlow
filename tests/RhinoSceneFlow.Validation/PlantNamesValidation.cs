using RhinoSceneFlow.Core;
internal static class PlantNamesValidation
{
    internal static void Run()
    {
        void Check(bool ok,string message){if(!ok)throw new Exception("Plant names: "+message);}
        var root=Directory.CreateTempSubdirectory("SceneFlow-names-").FullName;var lib=new MaterialLibrary(root);string png=Path.Combine(root,"metadata-fixture.png");File.WriteAllBytes(png,[1,2,3]);
        var a=lib.Import(new(){Name="美国红枫",Plant=new(){ScientificName="Acer rubrum",Family="Sapindaceae",Genus="Acer",Sources=["https://plants.ces.ncsu.edu/plants/acer-rubrum/"],SpacingMeters=15}},new Dictionary<string,string>{{"baseColor",png}});
        Check(PlantNames.Display(a,"zh")=="美国红枫"&&PlantNames.Display(a,"en")=="Acer rubrum","legacy fallback must never expose Chinese as an English name");
        var hash=a.Sha256["baseColor"];PlantNames.Apply(lib,[a],[new(a.Id,"美国红枫","Red maple")]);var named=lib.Get(a.Id);
        Check(named.Revision==a.Revision&&named.CatalogRevision==a.CatalogRevision+1&&named.Sha256["baseColor"]==hash&&named.Plant!.ScientificName=="Acer rubrum"&&named.Plant.SpacingMeters==15&&named.HeightMeters==a.HeightMeters,"localization changed appearance/identity/defaults");
        Check(PlantNames.Display(named,"en")=="Red maple"&&PlantNames.Display(named,"zh-CN")=="美国红枫","localized display");
        try{PlantNames.Apply(lib,[a],[new(a.Id,"旧名","Stale")]);throw new Exception("Stale plan accepted");}catch(InvalidOperationException){}
        PlantNames.Apply(lib,[named],[new(a.Id,"覆盖名字","Overwrite")]);Check(lib.Get(a.Id).Plant!.Names["en"]=="Red maple","existing translated/custom labels overwritten");
        Console.WriteLine("PASS: plant bilingual names preserve Latin identity, appearance, defaults and stale catalog guards.");
    }
}
