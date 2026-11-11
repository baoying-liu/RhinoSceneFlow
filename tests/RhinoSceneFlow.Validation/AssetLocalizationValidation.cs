using System.Text.Json;
using RhinoSceneFlow.Core;
internal static class AssetLocalizationValidation
{
    private static void Require(bool ok,string message){if(!ok)throw new Exception(message);}
    internal static void Run()
    {
        string root=Directory.CreateTempSubdirectory("SceneFlow-language-validation-").FullName;
        try
        {
            var library=new MaterialLibrary(root);string image=Path.Combine(root,"texture.png");File.WriteAllBytes(image,[1,2,3,4]);
            MaterialAsset Import(string name)=>library.Import(new(){Name=name,Category="石材",Tags=["自然","粗糙"],Randomization=new(){Reason="保留纹理"}},new Dictionary<string,string>{{"baseColor",image}});
            MaterialAsset first=Import("浅灰石灰石"),second=Import("深灰石灰石");
            CatalogLabel Plan(MaterialAsset a,string name="Light grey limestone")=>new(a.Id,a.Name,a.Category,a.Tags){Localizations=[new("zh",a.Name,"石材",["自然","粗糙"],"保留纹理"),new("en",name,"Stone",["Natural","Rough"],"Keep the texture")]};
            Require(!AssetLocalization.Complete(first)&&AssetLocalization.Name(first,"en")==first.Name,"Legacy assets must retain authored fallback.");
            var source=JsonSerializer.Serialize(first,MaterialLibrary.Json);var result=AssetLocalization.Apply(library,[first],[Plan(first)])[0];
            Require(AssetLocalization.Complete(result)&&AssetLocalization.Name(result,"en-US")=="Light grey limestone"&&AssetLocalization.Category(result,"en")=="Stone"&&AssetLocalization.Tag(result,"粗糙","en")=="Rough","Saved language fields not used.");
            Require(result.Name==first.Name&&result.Category==first.Category&&result.Tags.SequenceEqual(first.Tags)&&result.Revision==first.Revision&&result.CatalogRevision==first.CatalogRevision+1,"Translation changed canonical/appearance identity.");
            var originalAppearance=MaterialLibrary.Clone(result);originalAppearance.Localizations=[];originalAppearance.CatalogRevision=first.CatalogRevision;
            Require(JsonSerializer.Serialize(originalAppearance,MaterialLibrary.Json)==source,"Translation changed non-language fields.");
            Require(AssetLocalization.Matches(result,"rough limestone","zh")&&MaterialCatalog.Filter([result],"Rough",category:"石材",tag:"粗糙").Length==1,"All-language search or canonical filter keys failed.");
            library.Verify(result);Require(library.MapPath(result,"baseColor")==library.MapPath(first,"baseColor"),"Texture path changed.");
            var repeated=AssetLocalization.Apply(library,[result],[Plan(result,"Unwanted replacement")])[0];
            Require(repeated.CatalogRevision==result.CatalogRevision&&AssetLocalization.Name(repeated,"en")=="Light grey limestone","Backfill overwrote existing valid translation.");
            bool rejected=false;try{AssetLocalization.Apply(library,[first],[Plan(first)]);}catch(InvalidOperationException){rejected=true;}Require(rejected,"Stale localization accepted.");
            string beforeFirst=File.ReadAllText(Path.Combine(library.AssetDirectory(result.Id),"asset.json"));string beforeSecond=File.ReadAllText(Path.Combine(library.AssetDirectory(second.Id),"asset.json"));
            rejected=false;try{AssetLocalization.Apply(library,[result,second],[Plan(result),Plan(second) with{Name="unexpected rename"}]);}catch(InvalidDataException){rejected=true;}
            Require(rejected&&beforeFirst==File.ReadAllText(Path.Combine(library.AssetDirectory(result.Id),"asset.json"))&&beforeSecond==File.ReadAllText(Path.Combine(library.AssetDirectory(second.Id),"asset.json")),"Partial translation commit or canonical rename accepted.");
            var edited=library.UpdateLabels(result.Id,"用户改名",result.Category,[..result.Tags,"新标签"],result.CatalogRevision);
            Require(AssetLocalization.Name(edited,"en")=="用户改名"&&!AssetLocalization.Complete(edited)&&AssetLocalization.Category(edited,"en")=="Stone","Obsolete translated name or missing tag not detected.");
            string zip=Path.Combine(root,"asset.zip");library.ExportPackage(result.Id,zip);var unpacked=library.ImportPackage(zip);
            Require(unpacked.Localizations.Count==2&&unpacked.Localizations["en"].Name=="Light grey limestone"&&AssetLocalization.Name(unpacked,"en")=="用户改名","Portable package lost languages or source stamps.");
            var cleaned=MaterialCatalog.ValidatePlan([second],[Plan(second)]).Single();Require(cleaned.Localizations.Length==2,"Catalog normalization discarded language metadata.");
            var plant=new MaterialAsset{Name="河桦",Category="Betulaceae",Tags=["乔木"],Plant=new(){ScientificName="Betula nigra",Names=new(){{"zh","河桦"},{"en","River birch"}}}};
            AssetLocalization.SetDraft(plant,[new("zh","河桦","Betulaceae",["乔木"],""),new("en","River birch","Betulaceae",["Tree"],"")]);
            Require(PlantNames.Display(plant,"en")=="River birch"&&plant.Plant.ScientificName=="Betula nigra","Plant common names and scientific identity confused.");
            rejected=false;try{AssetLocalization.SetDraft(second,[new("en","X","Stone",["Natural"],"")]);}catch(InvalidDataException){rejected=true;}Require(rejected,"Incomplete AI language output accepted.");
            Console.WriteLine("PASS: persistent asset languages, legacy/stale fallback, canonical filters, multilingual search, no-op backfill, conflict/atomic guards, package roundtrip and plant identity.");
        }
        finally{Directory.Delete(root,true);}
    }
}
