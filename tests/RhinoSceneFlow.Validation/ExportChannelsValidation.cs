using RhinoSceneFlow.Core;

static class ExportChannelsValidation
{
    public static void Run(string output)
    {
        void Check(bool value,string message){if(!value)throw new Exception(message);}
        string staging=Directory.CreateTempSubdirectory("SceneFlow-Channels-").FullName;
        try
        {
            using var red=new DiskPassImage(staging,8,8,[new("Red",new(0,0,0))],true);
            using var blue=new DiskPassImage(staging,8,8,[new("Blue",new(0,0,0))],true);
            byte[] r=Enumerable.Range(0,8).SelectMany(_=>new byte[]{255,0,0,255}).ToArray(),b=Enumerable.Range(0,8).SelectMany(_=>new byte[]{0,0,255,255}).ToArray();
            for(int y=0;y<8;y++){red.WriteRgbaRow(y,0,r);blue.WriteRgbaRow(y,0,b);}
            var stack=new ConfiguredStack(new("Hidden flat",red,Visible:false),new("Hidden folder",red,Folder:true,Visible:false),new("Visible blue",blue));
            Check(stack.CompositeChannel(0,3,3)==0&&stack.CompositeChannel(2,3,3)==255,"Hidden passes must not alter the compatibility composite.");
            var records=stack.Records();Check(!records[0].Visible&&!records[1].Visible&&records[2].Visible,"Folder eye must preserve children's own visibility.");
            PsdWriter.Save(Path.Combine(output,"channels-visibility.psd"),stack);
            Check(stack.GetVisibleLayers().Count==3,"Hidden pixel data must still be exported.");
            var camera=new CameraProjection(new(0,0,0),new(1,0,0),new(0,1,0),new(0,0,1),-1,1,-1,1,1,100,true);
            var surface=new TextureSurface("same","Same",new(255,255,255),new(1,1,[255,0,0]),false,1,new(30,70,110));
            var objects=new[]{new TextureObject("a","A",0),new TextureObject("b","B",0)};
            var triangles=new[]{new TextureTriangle(new(-1,-1,-5),new(1,-1,-5),new(1,1,-5),new(),new(),new(),0),new TextureTriangle(new(-1,-1,-5),new(1,1,-5),new(-1,1,-5),new(),new(),new(),1)};
            var samples=TexturedRasterizer.Render(24,24,camera,[surface],objects,triangles,flatColor:true);
            var all=samples.Grouped("all");var byMaterial=samples.Grouped("material");var byObject=samples.Grouped("object");
            Check(all.Groups.Count==1&&byObject.Groups.Count==2&&byMaterial.Groups.Count==1,"Three grouping layouts.");
            for(int c=0;c<4;c++)for(int y=0;y<24;y++)for(int x=0;x<24;x++)Check(all.CompositeChannel(c,x,y)==byObject.CompositeChannel(c,x,y),"Grouping must preserve pixels.");
            Check(all.CompositeChannel(0,12,12)==30&&all.CompositeChannel(1,12,12)==70,"Representative material colour, not bitmap or shading.");
            var world=triangles.Select(t=>new WorldTriangle(t.A,t.B,t.C)).ToArray();var geometry=new PlantOccluders(world,camera.Origin);
            var settings=new BillboardSettings{Mode="free"};
            var tile=DepthRenderer.Render(24,24,camera,geometry,[],settings);Check(Math.Abs(tile.Distance[12*24+12]-5)<1e-8&&tile.Coverage[0]==4,"Camera-axis depth and ray clipping.");
            var plant=new PlantBillboard("p","Species","Plant",new(0,-.5,-2),1,1,.5,0,false,new(1,1,[0,255,0,255]));
            var plantDepth=DepthRenderer.Render(24,24,camera,geometry,[plant],settings);Check(Math.Abs(plantDepth.Distance[12*24+12]-2)<1e-8,"Plants participate at their billboard depth.");
            plant=plant with{Image=new(1,1,[0,255,0,0])};plantDepth=DepthRenderer.Render(24,24,camera,geometry,[plant],settings);Check(Math.Abs(plantDepth.Distance[12*24+12]-5)<1e-8,"Transparent plant holes reveal the geometry behind them.");
            using var depth=new DepthPassBuilder(staging,3,1);depth.WriteTile(2,0,new(1,1,[0],[0]));depth.WriteTile(0,0,new(2,1,[5,10],[4,4]));depth.Finish();
            Check(depth.Minimum==5&&depth.Maximum==10&&depth.Image.CompositeChannel(0,0,0)==255&&depth.Image.CompositeChannel(0,1,0)==0&&depth.Image.CompositeChannel(0,2,0)==0,"Global tiled normalization excludes empty background.");
            using var cancelled=new CancellationTokenSource();cancelled.Cancel();try{DepthRenderer.Render(24,24,camera,geometry,[],settings,cancelled.Token);throw new Exception("Depth cancellation ignored.");}catch(OperationCanceledException){}
        }
        finally{Directory.Delete(staging,true);}
        Console.WriteLine("PASS: PSD hidden pixels/folders/composite, colour grouping/representatives, linear depth, transparent plants, tiled range and cancellation.");
    }
}
