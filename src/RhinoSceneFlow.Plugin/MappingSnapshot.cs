using Rhino.Geometry;
using Rhino.Render;
using Rhino.Runtime;

namespace RhinoSceneFlow.Plugin;

/// <summary>TextureMapping does not round-trip through CommonObject.FromJSON in the
/// installed Rhino. Preserve its primitive, projection and transforms explicitly.</summary>
internal sealed class MappingSnapshot
{
    public TextureMappingType Type { get; set; }
    public bool Capped { get; set; }
    public TextureSpace Space { get; set; }
    public int Projection { get; set; }
    public double[] Primitive { get; set; } = [];
    public double[] Uvw { get; set; } = [];
    public string? Mesh { get; set; }
    public static string Capture(TextureMapping mapping)
    {
        var s=new MappingSnapshot{Type=mapping.MappingType,Capped=mapping.Capped,Space=mapping.TextureSpace,Projection=(int)mapping.Projection,Primitive=Array(mapping.PrimitiveTransform),Uvw=Array(mapping.UvwTransform)};
        if(s.Type==TextureMappingType.MeshMappingPrimitive)
        {if(!mapping.TryGetMappingMesh(out var mesh))throw new NotSupportedException("不能备份原自定义映射网格。");using(mesh)s.Mesh=mesh.ToJSON(new Rhino.FileIO.SerializationOptions());}
        else if(s.Type is not (TextureMappingType.PlaneMapping or TextureMappingType.BoxMapping or TextureMappingType.CylinderMapping or TextureMappingType.SphereMapping or TextureMappingType.SurfaceParameters))throw new NotSupportedException("原映射类型暂不能安全备份，请保留并使用其他对象："+s.Type);
        // Validate round-trip before touching the document.
        using var restored=s.Build();return MaterialService.Serialize(s);
    }
    public TextureMapping Build()
    {
        TextureMapping mapping;
        switch(Type)
        {
            case TextureMappingType.PlaneMapping:mapping=TextureMapping.CreatePlaneMapping(Plane.WorldXY,new(-1,1),new(-1,1),new(-1,1),Capped);break;
            case TextureMappingType.BoxMapping:mapping=TextureMapping.CreateBoxMapping(Plane.WorldXY,new(-1,1),new(-1,1),new(-1,1),Capped);break;
            case TextureMappingType.CylinderMapping:mapping=TextureMapping.CreateCylinderMapping(new Cylinder(new Circle(Plane.WorldXY,1),2),Capped);break;
            case TextureMappingType.SphereMapping:mapping=TextureMapping.CreateSphereMapping(new Sphere(Point3d.Origin,1));break;
            case TextureMappingType.SurfaceParameters:mapping=TextureMapping.CreateSurfaceParameterMapping();break;
            case TextureMappingType.MeshMappingPrimitive:
                using(var mesh=CommonObject.FromJSON(Mesh!) as Mesh??throw new InvalidDataException("原映射网格备份无效。"))mapping=TextureMapping.CreateCustomMeshMapping(mesh);break;
            default:throw new NotSupportedException("不支持的备份映射。");
        }
        mapping.Capped=Capped;mapping.TextureSpace=Space;mapping.Projection=(Rhino.Render.Projection)Projection;mapping.PrimitiveTransform=Matrix(Primitive);mapping.UvwTransform=Matrix(Uvw);return mapping;
    }
    private static double[] Array(Transform t)=>Enumerable.Range(0,16).Select(i=>t[i/4,i%4]).ToArray();
    private static Transform Matrix(double[] values){if(values.Length!=16)throw new InvalidDataException("映射变换备份无效。");var t=Transform.Identity;for(int i=0;i<16;i++)t[i/4,i%4]=values[i];return t;}
}
