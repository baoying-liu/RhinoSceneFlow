using System.Text.Json;
using RhinoSceneFlow.Core;

static class PlantLayoutValidation
{
    public static void Run()
    {
        static void Check(bool value,string message){if(!value)throw new Exception("Plant layout: "+message);}
        Guid a=Guid.NewGuid(),b=Guid.NewGuid();LayoutTriangle[] surface=[new(new(0,0,0),new(10,0,0),new(10,10,2)),new(new(0,0,0),new(10,10,2),new(0,10,2))];
        LayoutEdge[] edges=[new(new(0,0,0),new(10,0,0)),new(new(10,0,0),new(10,10,2)),new(new(10,10,2),new(0,10,2)),new(new(0,10,2),new(0,0,0))];
        PlantPaletteItem[] palette=[new(){Asset=a,SpacingMeters=.5,Weight=1},new(){Asset=b,SpacingMeters=1,Weight=3}];var s=new PlantLayoutSettings{Density=.6};LayoutManual[] manual=[new("hand",a,new(3,3,.6))];
        var original=PlantLayout.Generate(surface,edges,palette,manual,s);Check(original.Target==61&&original.Plants.Length==61,"area density incl slope and manual");Check(original.Plants.Count(p=>p.Manual)==1,"manual included exactly once");
        LayoutTriangle[] path=[new(new(4,-1,30),new(6,-1,30),new(6,11,40)),new(new(4,-1,30),new(6,11,40),new(4,11,40))];
        var exclusion=new PlantExclusions(path,.5);
        Check(exclusion.Contains(new(5,5,-100))&&exclusion.Contains(new(3.75,5,0))&&!exclusion.Contains(new(3.4,5,0)),"vertical footprint, slope and metric clearance");
        var avoided=PlantLayout.Generate(surface,edges,palette,manual,s,exclusions:exclusion);
        Check(avoided.Plants.Where(p=>!p.Manual).All(p=>!exclusion.Contains(p.Position)),"automatic plants never enter exclusion footprints");
        var handConflict=new LayoutManual("inside",a,new(5,5,1));
        var retainedConflict=PlantLayout.Generate(surface,edges,palette,[handConflict],s,exclusions:exclusion);
        Check(retainedConflict.Plants.Single(p=>p.Manual).Position==handConflict.Position,"existing manual conflicts are retained, not silently moved/deleted");
        Check(avoided.Plants.SequenceEqual(PlantLayout.Generate(surface,edges,palette,manual,s,exclusions:exclusion).Plants),"exclusion layout deterministic");
        double[] shifted=[1,0,0,4,0,1,0,0,0,0,1,0,0,0,0,1];
        Check(new PlantExclusions(path,0,shifted).Contains(new(1,5,0)),"moved group evaluated against fixed world exclusions");
        Check(!new PlantExclusions([],0).Contains(new(1,1,0)),"empty legacy exclusion default");
        var actual=new PlantExclusions(path,.2,geometryParts:[new(path,false)]);
        Check(!actual.Contains(new(5,5,0))&&actual.Contains(new(5,5,35)),"geometry mode respects height rather than infinite XY column");
        Vec3[] box=[new(0,0,0),new(2,0,0),new(2,2,0),new(0,2,0),new(0,0,2),new(2,0,2),new(2,2,2),new(0,2,2)];
        int[][] faces=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]];
        var boxTriangles=faces.Select(f=>new LayoutTriangle(box[f[0]],box[f[1]],box[f[2]])).ToArray();
        var obstacle=new PlantExclusions(boxTriangles,.1,geometryParts:[new(boxTriangles,true)]);
        Check(obstacle.Contains(new(1,1,1))&&!obstacle.Contains(new(1,1,4))&&obstacle.Contains(new(2.05,1,1))&&!obstacle.Contains(new(2.2,1,1)),"closed solid interior and true 3D safety distance");

        for(int i=0;i<original.Plants.Length;i++)for(int j=0;j<i;j++){var x=original.Plants[i];var y=original.Plants[j];double gap=(palette.First(p=>p.Asset==x.Asset).SpacingMeters+palette.First(p=>p.Asset==y.Asset).SpacingMeters)*.5;Check((x.Position-y.Position).Length>=gap-1e-9,"mixed spacing incl manual");}
        s.SizeSeed++;var resized=PlantLayout.Generate(surface,edges,palette,manual,s);Check(original.Plants.Select(p=>p.Position).SequenceEqual(resized.Plants.Select(p=>p.Position)),"size seed must not move layout");Check(original.Plants.Select(p=>p.Mirror).SequenceEqual(resized.Plants.Select(p=>p.Mirror)),"size seed must not change mirrors");Check(original.Plants.Where((p,i)=>p.Scale!=resized.Plants[i].Scale).Count()>30,"size stream changes");
        s.MirrorSeed++;var mirrored=PlantLayout.Generate(surface,edges,palette,manual,s);Check(resized.Plants.Select(p=>p.Scale).SequenceEqual(mirrored.Plants.Select(p=>p.Scale)),"mirror seed must not alter size");Check(resized.Plants.Where((p,i)=>p.Mirror!=mirrored.Plants[i].Mirror).Count()>10,"mirror stream changes");
        s.LayoutSeed++;var moved=PlantLayout.Generate(surface,edges,palette,manual,s);Check(moved.Plants[0].Position==manual[0].Position,"layout must preserve hand positions");Check(original.Plants[1].Position!=moved.Plants[1].Position,"layout seed changes auto positions");
        s.Density=0;Check(PlantLayout.Generate(surface,edges,palette,manual,s).Plants.Length==1,"manual beyond target retained");
        var fixedId="custom:test";var fixedPlant=new LayoutManual(fixedId,Guid.NewGuid(),new(5,5,1),false,2.75,true);
        s.Density=.4;var customized=PlantLayout.Generate(surface,edges,palette,[fixedPlant],s,excluded:new HashSet<string>{"auto:0"});
        Check(customized.Plants.Length==customized.Target&&customized.Plants.Count(p=>p.Id==fixedId)==1&&!customized.Plants.Any(p=>p.Id=="auto:0"),"customized automatic instance counts toward target without original duplicate");
        s.LayoutSeed+=5;s.SizeSeed+=5;s.MirrorSeed+=5;s.MinScale=.8;s.MaxScale=1.8;
        var changed=PlantLayout.Generate(surface,edges,palette,[fixedPlant],s);var retained=changed.Plants.Single(p=>p.Id==fixedId);
        Check(retained.Position==fixedPlant.Position&&retained.Scale==2.75&&retained.Mirror&&retained.Asset==fixedPlant.Asset,"customized position/type/scale/mirror survive all group seeds and ranges");
        s.Density=.6;s.EdgeStrength=1;s.EdgeDistance=2;s.EdgeCurve=[0,0,.3,.8,1];var boundary=PlantLayout.Generate(surface,edges,palette,[new("edge",a,new(0,0,0))],s);Check(boundary.Plants[0].Scale<=.015,"manual edge size");
        s.EdgeStrength=0;s.OverrideSpacing=true;s.Density=8;var dense=PlantLayout.Generate(surface,edges,palette,[],s);Check(dense.Plants.Length==dense.Target,"override spacing reaches density");Check(dense.Plants.Count(p=>p.Asset==b)>dense.Plants.Count(p=>p.Asset==a)*2,"weighted mixture");
        var json=JsonSerializer.Serialize(original,MaterialLibrary.Json);Check(JsonSerializer.Deserialize<PlantLayoutResult>(json,MaterialLibrary.Json)!.Plants.SequenceEqual(original.Plants),"persist value snapshots without recursive vector properties");
        using var cancel=new CancellationTokenSource();cancel.Cancel();try{PlantLayout.Generate(surface,edges,palette,[],s,cancel.Token);throw new Exception("uncancelled");}catch(OperationCanceledException){}
        Console.WriteLine("Plant layout streams / spacing / manual / density / edge / weights / persistence / cancellation passed.");
    }
}
