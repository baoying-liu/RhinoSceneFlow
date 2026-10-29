using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using Rhino.Display;
using Rhino.Geometry;
using RhinoSceneFlow.Core;
namespace RhinoSceneFlow.Plugin;

/// <summary>Native preview cutout geometry: transparent texels emit no depth-writing rectangles.</summary>
internal sealed class PlantPreviewGeometry:IDisposable
{
    internal readonly Mesh[] Meshes=Enumerable.Range(0,8).Select(_=>new Mesh()).ToArray();
    internal readonly DisplayMaterial[] Materials;
    internal long Bytes {get;}
    internal PlantPreviewGeometry(string path,RgbaTexture image,int resolution)
    {
        string rgb=RgbPath(path,image);double scale=Math.Min(1,(double)resolution/Math.Max(image.Width,image.Height));int w=Math.Max(1,(int)Math.Ceiling(image.Width*scale)),h=Math.Max(1,(int)Math.Ceiling(image.Height*scale));
        for(int y=0;y<h;y++)
        {
            int x=0;
            int Level(int column){double a=image.Sample((column+.5)/w,1-(y+.5)/h).A;return a<.02?0:Math.Clamp((int)Math.Round(a*8),1,8);}
            while(x<w)
            {
                int first=x,level=Level(x++);while(x<w&&Level(x)==level)x++;if(level==0)continue;
                var mesh=Meshes[level-1];int i=mesh.Vertices.Count;float u0=(float)first/w,u1=(float)x/w,v0=1-(float)(y+1)/h,v1=1-(float)y/h;
                mesh.Vertices.Add(u0,v0,0);mesh.Vertices.Add(u1,v0,0);mesh.Vertices.Add(u1,v1,0);mesh.Vertices.Add(u0,v1,0);
                mesh.TextureCoordinates.Add(u0,v0);mesh.TextureCoordinates.Add(u1,v0);mesh.TextureCoordinates.Add(u1,v1);mesh.TextureCoordinates.Add(u0,v1);mesh.Faces.AddFace(i,i+1,i+2,i+3);
            }
        }
        foreach(var m in Meshes){m.Normals.ComputeNormals();m.Compact();}
        Materials=Enumerable.Range(1,8).Select(level=>
        {
            double transparency=1-level/8.0;var material=new DisplayMaterial(System.Drawing.Color.White,transparency){IsTwoSided=true,BackDiffuse=System.Drawing.Color.White,BackTransparency=transparency};material.SetBitmapTexture(rgb,true);material.SetBitmapTexture(rgb,false);return material;
        }).ToArray();
        double rgbScale=Math.Min(1,2048.0/Math.Max(image.Width,image.Height));Bytes=(long)(image.Width*rgbScale)*(long)(image.Height*rgbScale)*4+Meshes.Sum(m=>(long)m.Vertices.Count*48+(long)m.Faces.Count*16);
    }
    private static string RgbPath(string path,RgbaTexture image)
    {
        string target=Path.Combine(Path.GetDirectoryName(path)!,Path.GetFileNameWithoutExtension(path)+"_preview_rgb_2048.png");if(File.Exists(target))return target;
        if(Math.Max(image.Width,image.Height)>2048)
        {
            double scale=2048.0/Math.Max(image.Width,image.Height);int w=Math.Max(1,(int)(image.Width*scale)),h=Math.Max(1,(int)(image.Height*scale));var rgba=new byte[w*h*4];
            for(int y=0;y<h;y++)for(int x=0;x<w;x++){var value=image.Sample((x+.5)/w,1-(y+.5)/h);int p=(y*w+x)*4;rgba[p]=(byte)Math.Clamp(Math.Round(value.R*255),0,255);rgba[p+1]=(byte)Math.Clamp(Math.Round(value.G*255),0,255);rgba[p+2]=(byte)Math.Clamp(Math.Round(value.B*255),0,255);rgba[p+3]=(byte)Math.Clamp(Math.Round(value.A*255),0,255);}image=new(w,h,rgba);
        }
        int count=image.Width*image.Height;var colors=new byte[count*3];var known=new bool[count];var queue=new int[count];int head=0,tail=0;
        for(int p=0;p<count;p++)if(image.Pixels[p*4+3]>4){known[p]=true;queue[tail++]=p;for(int c=0;c<3;c++)colors[p*3+c]=image.Pixels[p*4+c];}
        // Extend edge color through transparent RGB so bilinear filtering cannot introduce black/white halos.
        while(head<tail)
        {
            int p=queue[head++],x=p%image.Width,y=p/image.Width;
            void Fill(int n){if(known[n])return;known[n]=true;queue[tail++]=n;for(int c=0;c<3;c++)colors[n*3+c]=colors[p*3+c];}
            if(x>0)Fill(p-1);if(x+1<image.Width)Fill(p+1);if(y>0)Fill(p-image.Width);if(y+1<image.Height)Fill(p+image.Width);
        }
        string temp=target+"."+Guid.NewGuid().ToString("N")+".tmp";
        try
        {
            using var bitmap=new System.Drawing.Bitmap(image.Width,image.Height,PixelFormat.Format24bppRgb);var bits=bitmap.LockBits(new(0,0,image.Width,image.Height),ImageLockMode.WriteOnly,PixelFormat.Format24bppRgb);
            try{var row=new byte[Math.Abs(bits.Stride)];for(int y=0;y<image.Height;y++){for(int x=0;x<image.Width;x++)for(int c=0;c<3;c++)row[x*3+c]=colors[(y*image.Width+x)*3+2-c];Marshal.Copy(row,0,bits.Scan0+y*bits.Stride,row.Length);}}finally{bitmap.UnlockBits(bits);}
            using(var file=new FileStream(temp,FileMode.CreateNew,FileAccess.Write,FileShare.None))bitmap.Save(file,ImageFormat.Png);
            try{File.Move(temp,target,false);}catch(IOException) when(File.Exists(target)){}
        }
        finally{if(File.Exists(temp))File.Delete(temp);}return target;
    }
    public void Dispose(){foreach(var m in Meshes)m.Dispose();foreach(var m in Materials)m.Dispose();}
}
