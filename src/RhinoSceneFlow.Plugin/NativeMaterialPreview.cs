using Rhino;
using Rhino.Render;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

/// <summary>Rhino native RDK thumbnails, detached content; no document objects or RhinoViews.</summary>
public static class NativeMaterialPreview
{
    public static System.Drawing.Bitmap Render(MaterialAsset asset)
    {
        if(RhinoApp.InvokeRequired)throw new InvalidOperationException("Use the UI thread.");
        using var native=new Rhino.DocObjects.Material();native.ToPhysicallyBased();
        native.PhysicallyBased.BaseColor=new Rhino.Display.Color4f(System.Drawing.Color.White);native.PhysicallyBased.Roughness=asset.Roughness;native.PhysicallyBased.Metallic=asset.Metallic;
        foreach(var slot in asset.Maps.Keys)
        {
            using var texture=new Rhino.DocObjects.Texture{FileName=MaterialService.Library.MapPath(asset,slot),Enabled=true};
            var type=slot switch{"roughness"=>Rhino.DocObjects.TextureType.PBR_Roughness,"metallic"=>Rhino.DocObjects.TextureType.PBR_Metallic,"normal"=>Rhino.DocObjects.TextureType.Bump,_=>Rhino.DocObjects.TextureType.PBR_BaseColor};native.PhysicallyBased.SetTexture(texture,type);
        }
        using var content=RenderMaterial.FromMaterial(native,RhinoDoc.ActiveDoc);
        using var appearance=new PreviewAppearance(IntPtr.Zero);
        using var data=new SceneServerData(appearance,SceneServerDataUsage.Synchronous);
        using var server=content.NewPreviewSceneServer(data);
        var result=Rhino.Commands.Result.Failure;
        var image=RenderContent.GenerateQuickContentPreview(content,320,220,server,false,99,ref result);
        if(image==null||result!=Rhino.Commands.Result.Success){image?.Dispose();throw new InvalidOperationException("Rhino 材质预览未完成；可查看贴图预览并重试。");}
        return image;
    }
}
