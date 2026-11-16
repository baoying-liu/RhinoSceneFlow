using Rhino.DocObjects;
using Rhino.Render;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

internal static class MaterialEmission
{
    internal static string Signature(RenderMaterial? render)=>render?.GetParameter("pbr-emission") is Rhino.Display.Color4f c?$"{c.R:R}:{c.G:R}:{c.B:R}":"";
    internal static EmissionSettings Read(RenderMaterial? render,Material native)
    {
        var c=native.IsPhysicallyBased?native.PhysicallyBased.Emission:new Rhino.Display.Color4f(native.EmissionColor);
        double maximum=Math.Max(c.R,Math.Max(c.G,c.B));
        double norm=maximum>0?maximum:1;
        byte Channel(double v)=>(byte)Math.Clamp(Math.Round(v/norm*255),0,255);
        return new(){Enabled=maximum>0,Color=maximum>0?$"#{Channel(c.R):X2}{Channel(c.G):X2}{Channel(c.B):X2}":"#FFF0D0",Intensity=Math.Clamp(maximum>0?maximum:1,0,100)};
    }
    internal static void Set(RenderMaterial material,EmissionSettings value)
    {
        value.Validate();var c=value.Rgb;float scale=value.Enabled?1:0;
        var color=new Rhino.Display.Color4f(c.R/255f*scale,c.G/255f*scale,c.B/255f*scale,1);
        if(!material.SetParameter("pbr-emission",color))throw new ArgumentException("This material does not support PBR emission.");
        if(material.GetParameter("emission-multiplier")!=null&&!material.SetParameter("emission-multiplier",value.Enabled?value.Intensity:0))throw new ArgumentException("Cannot set emission multiplier.");
    }
}
