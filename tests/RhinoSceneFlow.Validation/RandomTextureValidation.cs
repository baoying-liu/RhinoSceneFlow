using RhinoSceneFlow.Core;

internal static class RandomTextureValidation
{
    internal static void Run(string output)
    {
        byte[] pixels=new byte[32*16*3];new Random(319).NextBytes(pixels);var image=new RandomImage(32,16,pixels);
        double Distance((double R,double G,double B) a,(double R,double G,double B) b)=>Math.Max(Math.Abs(a.R-b.R),Math.Max(Math.Abs(a.G-b.G),Math.Abs(a.B-b.B)));
        foreach(string mode in new[]{"off","object","stochastic","macro","structured"})
        {
            var settings=new TextureRandomization{Mode=mode,Strength=.15,Tiles=4,Columns=4,Rows=2,Rotate=true};
            var sample=new RandomTextureSampler(settings,98,2,1);var copy=new RandomTextureSampler(MaterialLibrary.Clone(settings),98,2,1);
            if(sample.Span!=(mode is "off" or "object"?1:4))throw new Exception("Random physical repeat span changed.");
            for(int n=0;n<100;n++)
            {
                double u=n*.07931-.8,v=n*.17192-.6;
                foreach(string slot in new[]{"baseColor","roughness","metallic","normal"})
                {
                    var c=sample.Sample(image,u,v,slot);
                    if(Distance(c,copy.Sample(image,u,v,slot))>1e-12||Distance(c,sample.Sample(image,u+sample.Span,v-sample.Span,slot))>1e-8)throw new Exception("Non-deterministic or non-periodic random texture: "+mode+"/"+slot);
                    if(slot=="normal"&&Math.Abs(Math.Sqrt(Math.Pow(c.R*2-1,2)+Math.Pow(c.G*2-1,2)+Math.Pow(c.B*2-1,2))-1)>1e-8)throw new Exception("Random normal not normalized.");
                    if(mode is "macro" or "structured"&&slot=="roughness"&&Distance(c,image.Sample(u,v,false))>1e-12)throw new Exception("Structure-preserving mode displaced texture coordinates.");
                }
            }
        }
        var off=new RandomTextureSampler(new(){Mode="off"},0,1,1);
        for(int y=0;y<16;y++)for(int x=0;x<32;x++)
        {
            var c=off.Sample(image,(x+.5)/32,1-(y+.5)/16,"baseColor");int i=(y*32+x)*3;
            if(Math.Abs(RandomImage.Encode(c.R,true)-pixels[i])>1||Math.Abs(RandomImage.Encode(c.G,true)-pixels[i+1])>1||Math.Abs(RandomImage.Encode(c.B,true)-pixels[i+2])>1)throw new Exception("Off mode changed source pixels.");
        }
        var structured=new RandomTextureSampler(new(){Mode="structured",Columns=4,Rows=2,Strength=.5},51,1,1);
        for(int i=0;i<20;i++){double u=i*.137,v=i%2*.5;if(Distance(structured.Sample(image,u,v,"baseColor"),image.Sample(u,v,true))>1e-10)throw new Exception("Structured cell boundary changed.");}
        byte[] normal=[220,128,220];var nimage=new RandomImage(1,1,normal);bool quarter=false;
        for(int seed=0;seed<30;seed++)
        {
            var s=new TextureRandomization{Mode="object",Rotate=true};
            var a=new RandomTextureSampler(s,seed,2,1).Sample(nimage,.2,.3,"normal");
            var b=new RandomTextureSampler(s,seed,1,1).Sample(nimage,.2,.3,"normal");
            if(Math.Abs(a.G-.5)>.01)throw new Exception("Non-square physical texture was rotated by a quarter turn.");
            quarter|=Math.Abs(b.G-.5)>.2;
        }
        if(!quarter)throw new Exception("Square normal rotation was not exercised.");
        byte[] heights=new byte[128*64*3];for(int y=0;y<64;y++)for(int x=0;x<128;x++)for(int c=0;c<3;c++)heights[(y*128+x)*3+c]=(byte)(40+x+63-y);
        var heightImage=new RandomImage(128,64,heights);double dx=128/255.0,dy=64/255.0,length=Math.Sqrt(dx*dx+dy*dy+1);
        var heightNormal=new RandomImage(1,1,[RandomImage.Encode(.5-.5*dx/length,false),RandomImage.Encode(.5-.5*dy/length,false),RandomImage.Encode(.5+.5/length,false)]);int checkedNormals=0;
        for(int seed=0;seed<40;seed++)
        {
            var sample=new RandomTextureSampler(new(){Mode="object",Rotate=true},seed,1,1);const double e=.0001;
            double du=(sample.Sample(heightImage,.31+e,.47,"roughness").R-sample.Sample(heightImage,.31-e,.47,"roughness").R)/(2*e);
            double dv=(sample.Sample(heightImage,.31,.47+e,"roughness").R-sample.Sample(heightImage,.31,.47-e,"roughness").R)/(2*e);
            if(Math.Abs(du)>2||Math.Abs(dv)>2)continue;double n=Math.Sqrt(du*du+dv*dv+1);var actual=sample.Sample(heightNormal,.31,.47,"normal");
            if(Distance(actual,(.5-.5*du/n,.5-.5*dv/n,.5+.5/n))>.008)throw new Exception("Normal rotation disagrees with actual transformed height gradient.");checkedNormals++;
        }
        if(checkedNormals<20)throw new Exception("Insufficient transformed normal gradient checks.");
        var objectSettings=new TextureRandomization{Mode="object",Seed=123};Guid id=new("fdafda90-9e15-4763-b20d-a9239856a072");
        if(objectSettings.InstanceSeed(id)!=MaterialLibrary.Clone(objectSettings).InstanceSeed(id)||objectSettings.InstanceSeed(id)==objectSettings.InstanceSeed(Guid.Empty))throw new Exception("Object variant seed not stable/distinct.");
        var stochastic=new RandomTextureSampler(new(){Mode="stochastic",Strength=0},19,1,1);double sum=0,sum2=0,baseSum=0,baseSum2=0;
        for(int i=0;i<10000;i++){double u=i*.61803398875,v=i*.41421356237;double a=stochastic.Sample(image,u,v,"baseColor").R,b=image.Sample(u,v,true).R;sum+=a;sum2+=a*a;baseSum+=b;baseSum2+=b*b;}
        double ratio=(sum2/10000-Math.Pow(sum/10000,2))/(baseSum2/10000-Math.Pow(baseSum/10000,2));
        if(ratio<.65||ratio>1.45||Math.Abs(sum-baseSum)/10000>.035)throw new Exception("Stochastic blend lost excessive contrast/mean: "+ratio);
        Console.WriteLine("PASS: random modes, periodic boundaries/negative UV, deterministic object seeds, metric spans, color transfer, preserved structure and rotated unit normals.");
    }
}
