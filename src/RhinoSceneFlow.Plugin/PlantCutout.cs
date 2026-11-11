using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
namespace RhinoSceneFlow.Plugin;

internal static class PlantCutout
{
    internal static (string Path,double Width,double Anchor) Normalize(string input,string output,double height)
    {
        using var source=new Bitmap(input);if(source.Width>8192||source.Height>8192)throw new InvalidDataException("植物图片超过 8192 像素。");
        using var rgba=new Bitmap(source.Width,source.Height,PixelFormat.Format32bppArgb);using(var g=Graphics.FromImage(rgba))g.DrawImageUnscaled(source,0,0);
        int left=rgba.Width,top=rgba.Height,right=0,bottom=0,visible=0,clear=0;var row=new byte[rgba.Width*4];var bits=rgba.LockBits(new(0,0,rgba.Width,rgba.Height),ImageLockMode.ReadOnly,PixelFormat.Format32bppArgb);
        try{for(int y=0;y<rgba.Height;y++){Marshal.Copy(bits.Scan0+y*bits.Stride,row,0,row.Length);for(int x=0;x<rgba.Width;x++){byte alpha=row[x*4+3];if(alpha==0)clear++;if(alpha>2){visible++;left=Math.Min(left,x);right=Math.Max(right,x+1);top=Math.Min(top,y);bottom=Math.Max(bottom,y+1);}}}}
        finally{rgba.UnlockBits(bits);}
        if(clear<rgba.Width*rgba.Height*.01||visible<16)throw new InvalidDataException("植物素材需要真实透明背景与可见植株。");
        using var crop=rgba.Clone(new Rectangle(left,top,right-left,bottom-top),PixelFormat.Format32bppArgb);crop.Save(output,ImageFormat.Png);
        double weighted=0,total=0;for(int y=Math.Max(top,bottom-Math.Max(2,(bottom-top)/100));y<bottom;y++)for(int x=left;x<right;x++){double a=rgba.GetPixel(x,y).A;weighted+=(x+.5-left)*a;total+=a;}
        return(output,height*crop.Width/crop.Height,total>0?Math.Clamp(weighted/total/crop.Width,0,1):.5);
    }
}
