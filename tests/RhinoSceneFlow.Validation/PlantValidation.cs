using RhinoSceneFlow.Core;
internal static class PlantValidation
{
    internal static void Run(string folder)
    {
        PlantNamesValidation.Run();
        BotanicalSourceValidation.Run();
        Directory.CreateDirectory(folder);
        void Check(bool value,string message){if(!value)throw new Exception(message);}
        var camera=new CameraProjection(new(0,0,10),new(1,0,0),new(0,1,0),new(0,0,1),-2,2,-2,2,1,20,true);
        RgbaTexture Texture(byte r,byte g,byte b,byte a)=>new(2,2,Enumerable.Range(0,4).SelectMany(_=>new[]{r,g,b,a}).ToArray());
        var plants=new[]{new PlantBillboard("a","A species","front A",new(-1,-1,5),2,2,0,0,false,Texture(255,0,0,128)),new PlantBillboard("b","B species","middle B",new(-1,-1,4),2,2,0,0,false,Texture(0,0,255,255)),new PlantBillboard("c","A species","back A",new(-1,-1,3),2,2,0,0,false,Texture(0,255,0,255))};
        var wall=new[]{new WorldTriangle(new(0,-2,6),new(2,-2,6),new(2,2,6)),new WorldTriangle(new(0,-2,6),new(2,2,6),new(0,2,6))};
        var blockers=new PlantOccluders(wall,camera.Origin);var free=new BillboardSettings{Mode="free"};
        var individual=PlantRasterizer.Render(64,64,camera,plants,free,blockers,"individual");var species=PlantRasterizer.Render(64,64,camera,plants,free,blockers,"species");var all=PlantRasterizer.Render(64,64,camera,plants,free,blockers,"all");
        Check(individual.Groups.Count==3&&species.Groups.Count==2&&all.Groups.Count==1,"Plant grouping count failed.");
        Check(individual.LayerAlpha(1,20,32)==255,"Individual plant was clipped by another plant.");
        Check(species.LayerAlpha(0,20,32)>0&&species.LayerAlpha(1,20,32)>0,"Translucent foliage lost underlying species.");
        for(int y=0;y<64;y++)for(int x=0;x<64;x++)for(int c=0;c<4;c++)Check(Math.Abs(species.CompositeChannel(c,x,y)-all.CompositeChannel(c,x,y))<=1,"Species grouping changed flattened composite.");
        Check(all.CompositeChannel(3,36,32)==0&&individual.CompositeChannel(3,36,32)==0,"Non-plant wall did not cut plants.");
        Check(Math.Abs(all.CompositeChannel(0,20,32)-128)<=1&&Math.Abs(all.CompositeChannel(2,20,32)-127)<=1,"Premultiplied foliage compositing failed.");
        var edge=new RgbaTexture(2,1,[255,0,0,0,0,255,0,255]).Sample(.5,.5);Check(edge.R==0&&edge.G==1&&Math.Abs(edge.A-.5)<1e-8,"Transparent RGB contaminated alpha edge.");
        var axes=plants[0].Axes(camera,new(){Mode="z"});Check(Math.Abs(axes.Up.Z-1)<1e-12,"Z-only billboard tilted.");
        axes=plants[0].Axes(camera,new(){Mode="auto"});Check(Math.Abs(axes.Up.Dot(camera.Up)-1)<1e-10,"Top camera did not switch to free billboard.");
        var layout=PlantRasterizer.Layout(plants,"individual",camera);using var sparse=new SparseRgbImage(folder,64,64,individual.Groups);sparse.WriteTile(0,0,individual,CancellationToken.None);
        var hierarchy=new PlantHierarchy(sparse,"individual",layout.Species);var stack=new ConfiguredStack(new StyledPass("植物",hierarchy,Folder:true));
        var records=stack.Records();Check(records.Count(r=>r.Section==1)==3&&records.Count(r=>r.Section==0)==3,"Scientific-name PSD nesting failed.");
        PsdWriter.Save(Path.Combine(folder,"plants-individual.psd"),stack);
        foreach(var (name,image) in new[]{("species",species),("all",all)})PsdWriter.Save(Path.Combine(folder,"plants-"+name+".psd"),new ConfiguredStack(new StyledPass("植物",new PlantHierarchy(image,name,PlantRasterizer.Layout(plants,name,camera).Species),Folder:true)));
        Check(CodexPlantAgent.BotanicalSource("https://powo.science.kew.org/taxon/test")&&!CodexPlantAgent.BotanicalSource("https://kew.org.fake.example/a"),"Botanical source boundary failed.");
        var floor=new PlantOccluders([new WorldTriangle(new(-2,-2,0),new(2,-2,0),new(2,2,0)),new WorldTriangle(new(-2,-2,0),new(2,2,0),new(-2,2,0))],camera.Origin);
        var empty=FlatRasterizer.Render(64,64,[new("Shadow",new(90,90,90))],[]);
        var cutout=plants[0] with{Image=new RgbaTexture(2,1,[0,0,0,0,0,255,0,255])};
        var shadow=PlantShadows.Add(empty,camera,floor,[cutout],free,new(0,0,1));
        Check(shadow.LayerAlpha(0,20,32)==0&&shadow.LayerAlpha(0,44,32)==255,"Plant shadow used an opaque rectangle instead of source alpha.");
        var shadowGroups=new[]{new ColorGroup("Shadow",new(90,90,90))};
        ClipVertex P(double x,double y)=>new(x,y,.5,1);
        var existing=FlatRasterizer.Render(64,64,shadowGroups,new[]{new Triangle(P(-.7,-.7),P(.071,-.7),P(.071,.7),0),new Triangle(P(-.7,-.7),P(.071,.7),P(-.7,.7),0)});
        var combined=PlantShadows.Add(existing,camera,floor,[cutout],free,new(0,0,1));
        var separated=PlantShadows.Separate(existing,camera,floor,[cutout],free,new(0,0,1));
        var reconstructed=new ConfiguredStack(new StyledPass("plants only",separated),new StyledPass("geometry",existing));
        for(int y=0;y<64;y++)for(int x=0;x<64;x++)
        {
            Check(Math.Abs(reconstructed.CompositeChannel(3,x,y)-combined.CompositeChannel(3,x,y))<=1,"Separated shadow alpha did not reconstruct the union.");
            if(existing.CompositeChannel(3,x,y)==255)Check(separated.LayerAlpha(0,x,y)==0,"Plant shadows double-darkened opaque geometry shadows.");
        }
        var nested=new ConfiguredStack(new StyledPass("foliage",hierarchy),new StyledPass("Plant shadows",separated,"mul ",137));
        var nestedStack=new ConfiguredStack(new StyledPass("Plants",nested,Folder:true,PassThrough:true),new StyledPass("Shadow",existing,"mul "),new StyledPass("background",all));
        var flatStack=new ConfiguredStack(new StyledPass("foliage",hierarchy),new StyledPass("Plant shadows",separated,"mul ",137),new StyledPass("Shadow",existing,"mul "),new StyledPass("background",all));
        for(int y=0;y<64;y++)for(int x=0;x<64;x++)for(int c=0;c<4;c++)Check(nestedStack.CompositeChannel(c,x,y)==flatStack.CompositeChannel(c,x,y),"Pass-through plant group changed shadow blending.");
        var nestedRecords=nestedStack.Records();int lastFoliage=nestedRecords.ToList().FindLastIndex(r=>r.Section==0&&r.Name!="Plant shadows"&&r.Name!="Shadow"&&r.Name!="background");
        Check(nestedRecords[0].Name=="Plants"&&nestedRecords[0].Blend=="pass"&&nestedRecords[lastFoliage+2].Name=="Plant shadows","Plant shadows must follow all scientific-name folders inside Plants.");
        Check(nestedRecords.Single(r=>r.Name=="Plant shadows").Opacity==137,"Separated shadow style was lost.");
        PsdWriter.Save(Path.Combine(folder,"plants-separated-shadows.psd"),nestedStack);
        var hiddenNested=new ConfiguredStack(new StyledPass("Plant shadows",separated,"mul ",Visible:false));
        Check(hiddenNested.CompositeChannel(3,44,32)==0&&!hiddenNested.Records()[0].Visible,"Hidden plant shadows entered the composite.");
        bool bounded=false;
        try{PlantRasterizer.Render(512,512,camera,Enumerable.Range(0,600).Select(i=>plants[0] with{Id=i.ToString()}).ToArray(),free,blockers,"individual");}catch(InvalidOperationException e) when(e.Message.Contains("128 MiB")){bounded=true;}
        Check(bounded,"Dense individual plant layers were allowed an unbounded allocation.");
        var asymmetric=plants[0] with{Anchor=new(0,-1,5),AnchorU=.75,Mirror=true,Image=new RgbaTexture(2,1,[0,0,0,0,0,255,0,255])};
        var mirrored=PlantRasterizer.Render(64,64,camera,[asymmetric],free,new PlantOccluders([],camera.Origin),"all");
        Check(mirrored.LayerAlpha(0,32,32)>200,"Mirroring moved an asymmetric stem away from its planting anchor.");
        var grounded=plants[0] with{Anchor=new(-1,-1,0),Image=Texture(0,255,0,255)};
        var topView=PlantRasterizer.Render(64,64,camera,[grounded],new(){Mode="auto"},floor,"all");
        Check(topView.LayerAlpha(0,32,32)==255,"Top-facing plant coplanar with its ground was incorrectly clipped.");
        Console.WriteLine("PASS: botanical source gate, billboard axes, alpha edges, non-plant clipping, independent plants, interleaved species/all equality and nested PSD groups.");
    }
}
