using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Render;
using RhinoSceneFlow.Core;

namespace RhinoSceneFlow.Plugin;

/// <summary>UI-thread snapshot of actual effective materials and seam-correct mapped render meshes.</summary>
internal sealed class TextureSceneBuilder(RhinoDoc doc,bool colorsOnly=false,bool layerColors=false)
{
    internal readonly List<TextureSurface> Surfaces=[];
    internal readonly List<TextureObject> Objects=[];
    internal readonly List<TextureTriangle> Triangles=[];
    private readonly Dictionary<string,int> materials=[];
    private readonly Dictionary<string,PixelTexture> bitmaps=[];
    private long bytes;
    internal void Add(RhinoObject obj,Mesh[] meshes)
    {
        if(obj.Geometry is Brep b&&b.Faces.Any(f=>f.MaterialChannelIndex>0))throw new NotSupportedException($"{obj.Id} 使用面级多材质，材质贴图通道暂不支持。");
        string? binding=obj.Attributes.MaterialSource==ObjectMaterialSource.MaterialFromLayer
            ?doc.Layers[obj.Attributes.LayerIndex].GetUserString(MaterialService.BindingKey):obj.Attributes.GetUserString(MaterialService.BindingKey);
        if(!colorsOnly&&binding!=null&&!MaterialService.UvValid(doc,obj))throw new InvalidOperationException($"{obj.Attributes.Name} ({obj.Id}) 的真实世界 UV 缺失或已失效，请先在材质面板重新映射。");
        var render=obj.GetRenderMaterial(true);var legacy=render is null?obj.GetMaterial(true):null;
        using var native=render?.ToMaterial(RenderTexture.TextureGeneration.Disallow)??(legacy is null?new Material():new Material(legacy));
        if(!colorsOnly&&(native.Transparency>1e-6||(native.IsPhysicallyBased&&native.PhysicallyBased.Opacity<.999999)))throw new NotSupportedException($"{obj.Id} 使用透明材质，材质贴图通道暂只支持不透明材质。");
        // GetMaterial may manufacture a new simulation ID for every object. The
        // effective classic table index is its document identity, including ByLayer.
        int classicIndex=obj.Attributes.MaterialSource==ObjectMaterialSource.MaterialFromObject
            ?obj.Attributes.MaterialIndex:doc.Layers[obj.Attributes.LayerIndex].RenderMaterialIndex;
        string key=render!=null?"rdk:"+render.Id:"legacy-index:"+classicIndex;
        string groupKey=key;
        string name=render?.Name??legacy?.Name??"未指定材质";
        if(string.IsNullOrWhiteSpace(name))name="材质 "+key;
        if(binding!=null)
        {
            var value=MaterialService.Deserialize<MaterialBinding>(binding);
            if(value.Randomized&&name.StartsWith($"SceneFlow_{value.Asset:N}_r{value.Revision}_meter2_random_",StringComparison.Ordinal))groupKey=$"sceneflow-random:{value.Asset:N}:r{value.Revision}";
            if(name.StartsWith("SceneFlow_"+value.Asset.ToString("N")+"_r"+value.Revision+"_",StringComparison.Ordinal))
                try{name=MaterialService.Library.Get(value.Asset).Name;}catch(FileNotFoundException){}
        }
        if(!layerColors&&binding!=null)
        {
            var id=MaterialService.Deserialize<MaterialBinding>(binding).Asset;var asset=MaterialService.Library.Get(id);string slot=Seasons.Slot(asset,PlantService.CurrentSeason);
            if(slot!="baseColor"){var seasonBinding=MaterialService.Deserialize<MaterialBinding>(binding);string selected=RandomTextureService.SeasonalPath(asset,slot,obj.Attributes.MaterialSource==ObjectMaterialSource.MaterialFromLayer?doc.Layers[obj.Attributes.LayerIndex].Id:obj.Id,seasonBinding.Randomized);using var seasonalTexture=native.GetBitmapTexture();if(seasonalTexture!=null){seasonalTexture.FileName=selected;native.SetBitmapTexture(seasonalTexture);}else native.SetBitmapTexture(selected);}
        }
        var color=native.DiffuseColor;
        if(native.IsPhysicallyBased)
        {
            var c=native.PhysicallyBased.BaseColor;
            byte C(double v)=>(byte)Math.Clamp(Math.Round(v*255),0,255);color=Color.FromArgb(C(c.R),C(c.G),C(c.B));
        }
        if(layerColors){color=doc.Layers[obj.Attributes.LayerIndex].Color;key=groupKey="layer-color:"+color.ToArgb();name=$"#{color.R:X2}{color.G:X2}{color.B:X2} "+doc.Layers[obj.Attributes.LayerIndex].FullPath;}
        using var texture=native.GetBitmapTexture();bool textured=!layerColors&&texture is {Enabled:true};bool mapped=textured&&!colorsOnly;
        if(!materials.TryGetValue(key,out int material))
        {
            PixelTexture? bitmap=null;
            if(textured)
            {
                string path=texture!.FileName;
                if(!Path.IsPathFullyQualified(path)&&!string.IsNullOrEmpty(doc.Path))path=Path.Combine(Path.GetDirectoryName(doc.Path)!,path);
                if(!File.Exists(path))throw new FileNotFoundException($"材质“{name}”的颜色贴图不存在。",path);
                string cache=Path.GetFullPath(path)+"|"+texture.WrapU+"|"+texture.WrapV;
                if(!bitmaps.TryGetValue(cache,out bitmap)){bitmap=ReadBitmap(path,texture.WrapU==TextureUvwWrapping.Repeat,texture.WrapV==TextureUvwWrapping.Repeat);bitmaps.Add(cache,bitmap);}
            }
            // PBR base-color texture amount blends the constant and bitmap; it does not
            // multiply a 100% bitmap by the default gray constant. Classic Modulate does.
            bool modulate=!native.IsPhysicallyBased&&texture?.TextureCombineMode==TextureCombineMode.Modulate;
            double amount=native.IsPhysicallyBased&&render!=null?render.GetTextureAmountFromUsage(RenderMaterial.StandardChildSlots.PbrBaseColor)/100:1;
            if(!double.IsFinite(amount)||amount<0||amount>1)throw new NotSupportedException("颜色贴图混合量需为 0–100%。");
            var constant=new Rgb(color.R,color.G,color.B);Rgb representative=constant;
            if(bitmap!=null)
            {
                long r=0,g=0,blueSum=0;for(int i=0;i<bitmap.Rgb.Length;i+=3){r+=bitmap.Rgb[i];g+=bitmap.Rgb[i+1];blueSum+=bitmap.Rgb[i+2];}double count=bitmap.Rgb.Length/3;
                byte Mix(long sum,byte fallback)=>(byte)Math.Clamp(Math.Round(modulate?sum/count*fallback/255:sum/count*amount+fallback*(1-amount)),0,255);
                representative=new(Mix(r,constant.R),Mix(g,constant.G),Mix(blueSum,constant.B));
            }
            material=Surfaces.Count;materials.Add(key,material);Surfaces.Add(new(groupKey,name,constant,bitmap,modulate,amount,representative));
        }
        int owner=Objects.Count;string objectName=string.IsNullOrWhiteSpace(obj.Attributes.Name)?"物件 "+obj.Id.ToString()[..8]:obj.Attributes.Name+" ["+obj.Id.ToString()[..8]+"]";
        Objects.Add(new(obj.Id.ToString(),objectName,material));
        using var mapping=mapped?obj.GetTextureMapping(texture!.MappingChannelId,out _):null;
        Transform mappingTransform=Transform.Identity;if(mapped){using var check=obj.GetTextureMapping(texture!.MappingChannelId,out mappingTransform);}
        foreach(var source in meshes)
        {
            using var mesh=source.DuplicateMesh();
            if(mesh.Normals.Count!=mesh.Vertices.Count)mesh.Normals.ComputeNormals();
            if(mapped)
            {
                mesh.Unweld(0,true);
                if(mapping!=null&&MaterialService.ReadUv(obj)?.Version!=2)mesh.SetTextureCoordinates(mapping,mappingTransform,false,true);
                if(mesh.TextureCoordinates.Count!=mesh.Vertices.Count)throw new NotSupportedException($"{obj.Id} 缺少可用的贴图 UV，请先配置映射。");
            }
            var points=mesh.Vertices.Select(p=>new Vec3(p.X,p.Y,p.Z)).ToArray();
            var uv=new Uv[points.Length];
            if(mapped)for(int i=0;i<uv.Length;i++){var t=mesh.TextureCoordinates[i];var p=new Point3d(t.X,t.Y,0);p.Transform(texture!.UvwTransform);uv[i]=new(p.X,p.Y);}
            foreach(var face in mesh.Faces)
            {
                AddFace(face.A,face.B,face.C);if(face.IsQuad)AddFace(face.A,face.C,face.D);
            }
            void AddFace(int a,int b,int c)=>Triangles.Add(new(points[a],points[b],points[c],uv[a],uv[b],uv[c],owner));
        }
    }
    private PixelTexture ReadBitmap(string path,bool repeatU,bool repeatV)
    {
        using var source=new Bitmap(path);
        if(source.Width>8192||source.Height>8192)throw new NotSupportedException("颜色贴图每边最多 8192 像素。");
        long size=(long)source.Width*source.Height*3;if(bytes+size>536_870_912)throw new NotSupportedException("场景颜色贴图解码超过 512 MiB，请降低源图分辨率。");bytes+=size;
        using var image=source.Clone(new Rectangle(0,0,source.Width,source.Height),PixelFormat.Format32bppArgb);var data=new byte[(int)size];
        var bits=image.LockBits(new(0,0,image.Width,image.Height),ImageLockMode.ReadOnly,PixelFormat.Format32bppArgb);
        try
        {
            var row=new byte[image.Width*4];
            for(int y=0;y<image.Height;y++)
            {
                Marshal.Copy(bits.Scan0+y*bits.Stride,row,0,row.Length);
                for(int x=0;x<image.Width;x++){if(!colorsOnly&&row[x*4+3]!=255)throw new NotSupportedException("材质贴图通道暂不支持 PNG 透明裁切，请使用不透明颜色图。");int i=(y*image.Width+x)*3;data[i]=row[x*4+2];data[i+1]=row[x*4+1];data[i+2]=row[x*4];}
            }
        }
        finally{image.UnlockBits(bits);}
        return new(image.Width,image.Height,data,repeatU,repeatV);
    }
}
