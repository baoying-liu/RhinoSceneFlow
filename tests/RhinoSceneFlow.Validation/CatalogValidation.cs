using RhinoSceneFlow.Core;

internal static class CatalogValidation
{
    internal static void Run(string output)
    {
        var a=new MaterialAsset{Name="浅灰石灰岩",Category="石材",Tags=["自然","粗糙"]};var b=new MaterialAsset{Name="光滑灰金属",Category="金属",Tags=["光滑"]};
        if(MaterialCatalog.Filter([a,b],"灰","石材","粗糙").Single().Id!=a.Id||MaterialCatalog.Filter([a,b],tag:"粗糙",category:"金属").Length!=0)throw new Exception("Catalog filters must intersect.");
        void Reject(CatalogLabel[] plan){try{MaterialCatalog.ValidatePlan([a,b],plan);}catch(InvalidDataException){return;}throw new Exception("Invalid catalog plan accepted.");}
        Reject([new(a.Id,"石灰岩","石材",["自然"])]);Reject([new(a.Id,"A","石材",["自然"]),new(a.Id,"B","石材",["自然"])]);Reject([new(a.Id,"A","石材",[]),new(b.Id,"B","金属",["光滑"])]);
        var plan=MaterialCatalog.ValidatePlan([a,b],[new(a.Id," 石灰岩 "," 石材 ",["自然","自然","粗糙"]),new(b.Id,"灰金属","金属",["光滑"])]);if(plan[0].Tags.Length!=2||plan[0].Name!="石灰岩")throw new Exception("Catalog normalization failed.");
        // Real metadata writes, revision conflict rejection and immutable texture identity.
        string root=Directory.CreateTempSubdirectory("SceneFlow-catalog-validation-").FullName;var lib=new MaterialLibrary(root);string file=Path.Combine(root,"base.png");File.WriteAllBytes(file,[1,2,3]);
        var imported=lib.Import(a,new Dictionary<string,string>{{"baseColor",file}});var old=MaterialLibrary.Clone(imported);var map=imported.Maps["baseColor"];var hash=imported.Sha256["baseColor"];
        MaterialCatalog.Apply(lib,[imported],[new(imported.Id,"石灰岩 · 浅灰","石材",["自然"])]);var current=lib.Get(imported.Id);
        if(current.Id!=old.Id||current.WidthMeters!=old.WidthMeters||current.Maps["baseColor"]!=map||current.Sha256["baseColor"]!=hash||current.Revision!=old.Revision||current.CatalogRevision!=old.CatalogRevision+1)throw new Exception("Catalog changed appearance revision or material data.");
        try{MaterialCatalog.Apply(lib,[old],[new(old.Id,"stale","X",["X"])]);throw new Exception("Stale catalog accepted.");}catch(InvalidOperationException){}
        Console.WriteLine("PASS: catalog filter intersection, plan completeness/identity, normalized vocabulary, immutable textures/dimensions and stale revision rejection.");
    }
}
