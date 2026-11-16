using RhinoSceneFlow.Core;

static class EmissionValidation
{
    public static void Run(string output)
    {
        void Check(bool ok,string label){if(!ok)throw new Exception(label);}
        var camera=new CameraProjection(new(0,0,0),new(1,0,0),new(0,1,0),new(0,0,1),-1,1,-1,1,1,100,true);
        TextureSurface[] surfaces=[new("light","Lamp",new(255,160,40),null,Emissive:true),new("wall","Wall",new(240,240,240),null)];
        TextureObject[] objects=[new("a","Lamp A",0),new("b","Lamp B",0),new("w","Occluding wall",1)];
        var triangles=new List<TextureTriangle>();
        void Quad(double l,double t,double r,double b,double z,int owner){triangles.Add(new(new(l,t,z),new(r,t,z),new(r,b,z),new(),new(),new(),owner));triangles.Add(new(new(l,t,z),new(r,b,z),new(l,b,z),new(),new(),new(),owner));}
        Quad(-.8,-.7,0,.7,-5,0);Quad(.2,-.5,.7,.5,-5,1);Quad(-.8,-.7,-.4,.7,-3,2);
        var samples=TexturedRasterizer.Render(96,72,camera,surfaces,objects,triangles);
        var all=samples.Grouped("all",true);var split=samples.Grouped("object",true);var material=samples.Grouped("material",true);
        Check(split.Groups.Count==2&&material.Groups.Count==1,"Only emitters may create emission groups.");
        Check(all.CompositeChannel(3,14,36)==0&&all.CompositeChannel(3,40,36)>0,"Occluder must hide emission before bloom.");
        for(int c=0;c<4;c++)for(int y=0;y<72;y++)for(int x=0;x<96;x++)Check(all.CompositeChannel(c,x,y)==split.CompositeChannel(c,x,y),"Emission grouping changes visible pixels.");
        var black=samples.Grouped("all",true);
        var masked=TexturedRasterizer.Render(96,72,camera,[surfaces[0] with{Texture=new(1,1,[0,0,0])},surfaces[1]],objects,triangles).Grouped("all",true);
        Check(masked.CompositeChannel(3,40,36)==0,"Black emission mask must not create a black opaque layer.");
        var glow=new EmissionGlow(all,2);Check(glow.CompositeChannel(3,50,36)>0,"Bloom must expand outside the emitter.");
        var crop=new ImageWindow(all,35,0,61,72);var cropGlow=new EmissionGlow(crop,2);
        for(int c=0;c<4;c++)for(int y=0;y<72;y++)for(int x=6;x<61;x++)Check(glow.CompositeChannel(c,x+35,y)==cropGlow.CompositeChannel(c,x,y),"Halo tile boundary changed bloom.");
        var merged=new ConfiguredStack(new StyledPass("Emission",new CompositeOnlyImage(new ConfiguredStack(new StyledPass("Sources",all),new("Glow",glow,"scrn")),"Emission"),"hLit"));
        PsdWriter.Save(Path.Combine(output,"emission-merged.psd"),merged,overwrite:true);
        var grouped=new ConfiguredStack(new StyledPass("Emission",new ConfiguredStack(new StyledPass("Sources",split,Folder:true),new("Glow",new EmissionGlow(split,2),"scrn",Folder:true)),"hLit",Folder:true));
        PsdWriter.Save(Path.Combine(output,"emission-separated.psd"),grouped,overwrite:true);
        var hidden=new ConfiguredStack(new StyledPass("Emission",all,"hLit",Visible:false));Check(hidden.CompositeChannel(3,40,36)==0,"Hidden emission must not change composite.");
        using var cancelled=new CancellationTokenSource();cancelled.Cancel();try{_ = new EmissionGlow(all,2,cancelled.Token);throw new Exception("Bloom ignored cancellation.");}catch(OperationCanceledException){}
        foreach(var bad in new[]{double.NaN,-1,101})try{new EmissionSettings{Intensity=bad}.Validate();throw new Exception("Invalid emission accepted.");}catch(ArgumentException){}
        var clone=MaterialLibrary.Clone(new MaterialAsset{Emission=new(){Enabled=true,Color="#FFCC88",Intensity=3}});Check(clone.Emission.Color=="#FFCC88"&&clone.Emission.Intensity==3,"Emission metadata clone failed.");
        Console.WriteLine("PASS: occluded emission, grouping, halo tile continuity, PSD hierarchy/blend/visibility, metadata and cancellation.");
    }
}
