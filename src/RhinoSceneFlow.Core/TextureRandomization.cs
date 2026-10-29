using System.Security.Cryptography;
using System.Text.Json.Serialization;

namespace RhinoSceneFlow.Core;

public sealed class TextureRandomization
{
    public string Mode {get;set;}="off";
    public string RecommendedMode {get;set;}="off";
    public string Reason {get;set;}="尚未分析，可手动选择。";
    public string RecommendedBy {get;set;}="none";
    public int Seed {get;set;}=42;
    public double Strength {get;set;}=.15;
    public int Tiles {get;set;}=4;
    public bool Rotate {get;set;}
    public int Columns {get;set;}=1;
    public int Rows {get;set;}=1;
    public double RowOffset {get;set;}=.5;
    [JsonIgnore] public string ResolvedMode=>Mode=="auto"?RecommendedMode:Mode;
    public static bool ValidMode(string value)=>value is "off" or "object" or "stochastic" or "macro" or "structured";
    public void Validate()
    {
        if((Mode!="auto"&&!ValidMode(Mode))||!ValidMode(RecommendedMode)||!double.IsFinite(Strength)||Strength<0||Strength>.5||Tiles is not (2 or 4 or 8)||Columns is <1 or >128||Rows is <1 or >128||!double.IsFinite(RowOffset)||RowOffset<0||RowOffset>1||Reason==null||Reason.Length>600)throw new ArgumentException("随机配置无效：检查模式、色差、周期和行列。");
    }
    public int InstanceSeed(Guid id)
    {
        uint hash=2166136261;foreach(byte b in id.ToByteArray())hash=unchecked((hash^b)*16777619);
        return ResolvedMode=="object"?unchecked(Seed^(int)hash):Seed;
    }
}

public sealed class TextureBakeRequest
{
    public int Version {get;set;}=1;
    public string Key {get;set;}="";
    public Dictionary<string,string> Maps {get;set;}=[];
    public Dictionary<string,string> Sha256 {get;set;}=[];
    public TextureRandomization Settings {get;set;}=new();
    public int Seed {get;set;}
    public double WidthMeters {get;set;}
    public double HeightMeters {get;set;}
    public string OutputDirectory {get;set;}="";
}
public sealed class TextureBakeManifest
{
    public int Version {get;set;}=1;
    public string Key {get;set;}="";
    public double WidthMeters {get;set;}
    public double HeightMeters {get;set;}
    public Dictionary<string,string> Maps {get;set;}=[];
    public Dictionary<string,string> Sha256 {get;set;}=[];
}

/// <summary>Periodic, metric-preserving sampling. No geometry or renderer access.</summary>
public sealed class RandomTextureSampler
{
    private readonly TextureRandomization settings;
    private readonly int seed;
    private readonly string mode;
    private readonly FastNoiseLite noise;
    private readonly bool rotateQuarter;
    public int Span=>mode is "off" or "object"?1:settings.Tiles;
    public RandomTextureSampler(TextureRandomization settings,int seed,double widthMeters,double heightMeters)
    {
        settings.Validate();this.settings=MaterialLibrary.Clone(settings);this.seed=seed;mode=settings.ResolvedMode;
        rotateQuarter=Math.Abs(widthMeters-heightMeters)<1e-9*Math.Max(widthMeters,heightMeters);
        noise=new(seed);noise.SetNoiseType(FastNoiseLite.NoiseType.OpenSimplex2);noise.SetFrequency(2f/Span);
    }
    private static int Mod(int x,int n)=>(x%n+n)%n;
    private uint Hash(int x,int y)
    {uint h=unchecked((uint)seed^((uint)x*0x9E3779B9u)^((uint)y*0x85EBCA6Bu));h^=h>>16;h*=0x7FEB352Du;h^=h>>15;h*=0x846CA68Bu;return h^(h>>16);}
    private static double Unit(uint h)=>(h&0xFFFFFF)/16777216.0;
    private static double Smooth(double t){t=Math.Clamp(t,0,1);return t*t*(3-2*t);}
    private double Macro(double u,double v)
    {
        u-=Math.Floor(u/Span)*Span;v-=Math.Floor(v/Span)*Span;double x=Smooth(u/Span),y=Smooth(v/Span);
        double N(double a,double b)=>noise.GetNoise((float)a,(float)b);
        return (1-y)*((1-x)*N(u,v)+x*N(u-Span,v))+y*((1-x)*N(u,v-Span)+x*N(u-Span,v-Span));
    }
    private (double U,double V,int Turn) Transform(double u,double v,uint hash)
    {
        int turn=!settings.Rotate?0:rotateQuarter?(int)(hash%4):(int)(hash%2)*2;
        (u,v)=turn switch{1=>(-v,u),2=>(-u,-v),3=>(v,-u),_=>(u,v)};
        return(u+Unit(hash^0xD168AAAD),v+Unit(hash^0xAF723597),turn);
    }
    public (double R,double G,double B) Sample(RandomImage image,double u,double v,string slot)
    {
        var sum=(R:0.0,G:0.0,B:0.0);double squared=0;
        void Add(double su,double sv,int turn,double weight)
        {
            var c=image.Sample(su,sv,slot=="baseColor");
            if(slot=="normal")
            {
                double nx=c.R*2-1,ny=c.G*2-1,nz=c.B*2-1;
                (nx,ny)=turn switch{1=>(ny,-nx),2=>(-nx,-ny),3=>(-ny,nx),_=>(nx,ny)};
                c=(nx,ny,nz);
            }
            sum.R+=c.R*weight;sum.G+=c.G*weight;sum.B+=c.B*weight;squared+=weight*weight;
        }
        if(mode=="stochastic")
        {
            int ix=(int)Math.Floor(u),iy=(int)Math.Floor(v);double tx=Smooth(u-ix),ty=Smooth(v-iy);
            for(int y=0;y<2;y++)for(int x=0;x<2;x++)
            {
                uint h=Hash(Mod(ix+x,Span),Mod(iy+y,Span));var p=Transform(u,v,h);
                Add(p.U,p.V,p.Turn,(x==0?1-tx:tx)*(y==0?1-ty:ty));
            }
            // Variance correction prevents the usual washed-out average. This is
            // not claimed as exact histogram-preserving synthesis.
            if(slot=="baseColor"){double scale=1/Math.Sqrt(squared);var m=image.Mean;sum=(m.R+(sum.R-m.R)*scale,m.G+(sum.G-m.G)*scale,m.B+(sum.B-m.B)*scale);}
        }
        else if(mode=="object"){var p=Transform(u,v,Hash(0,0));Add(p.U,p.V,p.Turn,1);}
        else Add(u,v,0,1);
        if(slot=="normal")
        {double length=Math.Sqrt(sum.R*sum.R+sum.G*sum.G+sum.B*sum.B);return length<1e-9?(.5,.5,1):(.5+.5*sum.R/length,.5+.5*sum.G/length,.5+.5*sum.B/length);}
        if(slot=="baseColor"&&mode!="off")
        {
            double amount=0;
            if(mode=="object")amount=2*Unit(Hash(0,0)^0x49BC2315)-1;
            else if(mode=="structured")
            {
                double row=-v*settings.Rows;int iy=(int)Math.Floor(row);double column=u*settings.Columns+(Mod(iy,2)*settings.RowOffset);int ix=(int)Math.Floor(column);
                double edge=Math.Min(Math.Min(column-ix,1-column+ix),Math.Min(row-iy,1-row+iy));
                amount=(2*Unit(Hash(Mod(ix,Span*settings.Columns),Mod(iy,Span*settings.Rows)))-1)*Smooth((edge-.035)/.08);
            }
            else amount=Macro(u,v);
            double tint=1+settings.Strength*amount;sum=(sum.R*tint,sum.G*tint,sum.B*tint);
        }
        return sum;
    }
}

public sealed class RandomImage
{
    private static readonly double[] linear=Enumerable.Range(0,256).Select(i=>{double c=i/255.0;return c<=.04045?c/12.92:Math.Pow((c+.055)/1.055,2.4);}).ToArray();
    private static readonly byte[] encoded=Enumerable.Range(0,65536).Select(i=>{double c=i/65535.0;return (byte)Math.Clamp(Math.Round(255*(c<=.0031308?12.92*c:1.055*Math.Pow(c,1/2.4)-.055)),0,255);}).ToArray();
    public int Width{get;}public int Height{get;}public byte[] Pixels{get;}
    public (double R,double G,double B) Mean{get;}
    public RandomImage(int width,int height,byte[] rgb)
    {
        if(width<1||height<1||rgb.Length!=(long)width*height*3)throw new ArgumentException("Invalid RGB image.");
        Width=width;Height=height;Pixels=rgb;var mean=(R:0.0,G:0.0,B:0.0);
        for(int i=0;i<rgb.Length;i+=3){mean.R+=linear[rgb[i]];mean.G+=linear[rgb[i+1]];mean.B+=linear[rgb[i+2]];}double n=(double)width*height;Mean=(mean.R/n,mean.G/n,mean.B/n);
    }
    public (double R,double G,double B) Sample(double u,double v,bool srgb)
    {
        double px=(u-Math.Floor(u))*Width-.5,py=(1-(v-Math.Floor(v)))*Height-.5;int x=(int)Math.Floor(px),y=(int)Math.Floor(py);double tx=px-x,ty=py-y;
        int Mod(int a,int n)=>(a%n+n)%n;
        double C(int dx,int dy,int channel){byte value=Pixels[(Mod(y+dy,Height)*Width+Mod(x+dx,Width))*3+channel];return srgb?linear[value]:value/255.0;}
        double Channel(int c)=>(1-ty)*((1-tx)*C(0,0,c)+tx*C(1,0,c))+ty*((1-tx)*C(0,1,c)+tx*C(1,1,c));
        return(Channel(0),Channel(1),Channel(2));
    }
    public static byte Encode(double value,bool srgb)=>srgb?encoded[(int)Math.Clamp(Math.Round(value*65535),0,65535)]:(byte)Math.Clamp(Math.Round(value*255),0,255);
    public static string Hash(string path){using var file=File.OpenRead(path);return Convert.ToHexString(SHA256.HashData(file));}
}
