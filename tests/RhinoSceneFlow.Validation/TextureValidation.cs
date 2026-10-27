using RhinoSceneFlow.Core;

static class TextureValidation
{
    public static void Run(string output)
    {
        void Check(bool ok,string message){if(!ok)throw new Exception(message);}
        var tex=new PixelTexture(2,2,[255,0,0,0,255,0,0,0,255,255,255,255]);
        Check(tex.Sample(new(.25,.75))==new Rgb(255,0,0),"Texture vertical orientation.");
        Check(tex.Sample(new(-.75,1.75))==tex.Sample(new(.25,.75)),"Negative/repeated UV.");
        Check((tex with{RepeatU=false,RepeatV=false}).Sample(new(-2,2))==new Rgb(255,0,0),"Clamped UV.");
        var camera=new CameraProjection(new(0,0,0),new(1,0,0),new(0,1,0),new(0,0,1),-1,1,-1,1,1,100,false);
        var surfaces=new TextureSurface[]{new("same","Same",new(255,255,255),tex),new("other","Same",new(40,90,180),null)};
        var objects=new TextureObject[]{new("a","A",0),new("b","B",0),new("c","C",1)};
        Vec3 a=new(-1.6,-1.6,-2),b=new(3.2,-3.2,-4),c=new(0,1.6,-2);
        var triangle=new TextureTriangle(a,b,c,new(0,0),new(1,0),new(.5,1),0);
        var pbr=new TextureSurface[]{new("pbr","PBR",new(128,128,128),tex,false)};
        var solidUv=triangle with{UA=new(.25,.75),UB=new(.25,.75),UC=new(.25,.75)};
        var pbrImage=TexturedRasterizer.Render(64,48,camera,pbr,[objects[0]],[solidUv]).Grouped("material");
        Check(pbrImage.CompositeChannel(0,32,24)==255&&pbrImage.CompositeChannel(1,32,24)==0,"100% PBR bitmap must replace default gray.");
        pbrImage=TexturedRasterizer.Render(64,48,camera,[pbr[0] with{TextureAmount=.5}],[objects[0]],[solidUv]).Grouped("material");
        Check(pbrImage.CompositeChannel(0,32,24)==192&&pbrImage.CompositeChannel(1,32,24)==64,"PBR bitmap amount blends the constant color.");
        var samples=TexturedRasterizer.Render(64,48,camera,surfaces,objects,[triangle]);
        var merged=samples.Grouped("material");var split=samples.Grouped("object");
        Check(merged.Groups.Count==2&&split.Groups.Count==3,"Group by identity, never duplicate names.");
        // Independent world-space ray/plane intersection and barycentric UV oracle.
        for(int y=20;y<27;y++)for(int x=29;x<35;x++)
        {
            var sum=new int[3];
            for(int sy=0;sy<2;sy++)for(int sx=0;sx<2;sx++)
            {
                Vec3 ray=new(2*(x+(sx+.5)/2)/64-1,1-2*(y+(sy+.5)/2)/48,-1);
                var e=b-a;var f=c-a;var n=e.Cross(f);var hit=ray*(a.Dot(n)/ray.Dot(n))-a;
                double ee=e.Dot(e),ef=e.Dot(f),ff=f.Dot(f),he=hit.Dot(e),hf=hit.Dot(f),det=ee*ff-ef*ef;
                double wb=(he*ff-hf*ef)/det,wc=(hf*ee-he*ef)/det;
                var rgb=tex.Sample(new(wb+.5*wc,wc));sum[0]+=rgb.R;sum[1]+=rgb.G;sum[2]+=rgb.B;
            }
            for(int ch=0;ch<3;ch++)Check(Math.Abs(merged.CompositeChannel(ch,x,y)-Math.Round(sum[ch]/4.0))<=1,"Perspective UV must match ray-plane oracle.");
        }
        var overlap=new[]{triangle,triangle with{Object=1,A=a*.5,B=b*.5,C=c*.5,UA=new(.25,.75),UB=new(.25,.75),UC=new(.25,.75)}};
        var occluded=TexturedRasterizer.Render(64,48,camera,surfaces,objects,overlap).Grouped("object");
        Check(occluded.GetVisibleLayers().Count==1,"Fully covered rear objects omitted.");
        var clip=TexturedRasterizer.Render(64,48,camera,surfaces,objects,[triangle with{A=new(-4,-1,-.5)}]).Grouped("material");
        Check(clip.GetVisibleLayers().Count==1,"Near and side clipping retain textured geometry.");
        var scene=new[]{triangle,triangle with{Object=1,A=new(-.3,-.3,-1.5),B=new(1.2,-.3,-1.5),C=new(.3,1,-1.5)},triangle with{Object=2,A=new(-2,-2,-3),B=new(2,-2,-3),C=new(-2,2,-3)}};
        samples=TexturedRasterizer.Render(64,48,camera,surfaces,objects,scene);merged=samples.Grouped("material");split=samples.Grouped("object");
        for(int y=0;y<48;y++)for(int x=0;x<64;x++)for(int ch=0;ch<4;ch++)Check(merged.CompositeChannel(ch,x,y)==split.CompositeChannel(ch,x,y),"Grouping cannot alter composite.");
        string stage=Directory.CreateTempSubdirectory("Texture-test-").FullName;
        try
        {
            foreach(var mode in new[]{"material","object"})
            {
                var source=samples.Grouped(mode);using var disk=new SparseRgbImage(stage,64,48,source.Groups);disk.WriteTile(0,0,source,default);
                for(int y=0;y<48;y++)for(int x=0;x<64;x++)for(int ch=0;ch<4;ch++)
                {
                    Check(disk.CompositeChannel(ch,x,y)==source.CompositeChannel(ch,x,y),"Sparse composite roundtrip.");
                    for(int g=0;g<source.Groups.Count;g++)Check(disk.LayerChannel(g,ch,x,y)==source.LayerChannel(g,ch,x,y),"Independent per-layer RGBA roundtrip.");
                }
                PsdWriter.Save(Path.Combine(output,"texture-"+mode+".psd"),new ConfiguredStack(new StyledPass("材质",disk,Folder:true)));
            }
            using var cancelled=new CancellationTokenSource();cancelled.Cancel();
            try{TexturedRasterizer.Render(64,48,camera,surfaces,objects,scene,cancelled.Token);throw new Exception("Cancellation ignored.");}catch(OperationCanceledException){}
            var reference=TexturedRasterizer.Render(1030,32,camera,surfaces,objects,scene).Grouped("object");
            using var tiled=new SparseRgbImage(stage,1030,32,reference.Groups);
            for(int left=0;left<1030;left+=1024)
            {
                int tw=Math.Min(1024,1030-left);
                var sub=camera with{Left=camera.Left+(camera.RightEdge-camera.Left)*left/1030,RightEdge=camera.Left+(camera.RightEdge-camera.Left)*(left+tw)/1030};
                tiled.WriteTile(left,0,TexturedRasterizer.Render(tw,32,sub,surfaces,objects,scene).Grouped("object"),default);
            }
            for(int y=0;y<32;y++)for(int x=0;x<1030;x++)for(int ch=0;ch<4;ch++)
            {
                Check(Math.Abs(tiled.CompositeChannel(ch,x,y)-reference.CompositeChannel(ch,x,y))<=1,"Tile frusta must preserve texture samples.");
                for(int g=0;g<reference.Groups.Count;g++)Check(Math.Abs(tiled.LayerChannel(g,ch,x,y)-reference.LayerChannel(g,ch,x,y))<=1,"Independent layer tile boundaries.");
            }
        }
        finally{Directory.Delete(stage,true);}
        Console.WriteLine("PASS: real RGB textures, perspective ray oracle, UV wrapping, clipping, shared occlusion, material/object grouping, sparse RGBA and PSD export.");
    }
}
