"""Research-only native display shadow captures on the fixed B test document."""
import clr,json,os,System,Rhino,math
from System.Drawing import Color,Size
from Rhino.Geometry import Point3d,BoundingBox
from Rhino.Display import DisplayModeDescription,DefinedViewportProjection
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'alternatives');os.makedirs(folder,exist_ok=True)
if doc.Objects.Count==0:
    source=Rhino.FileIO.File3dm.Read(os.path.join(OUTPUT_DIR,'shadows','Shadow-Test.3dm'))
    assert source is not None
    layer_map={}
    for old in source.AllLayers:
        layer=Rhino.DocObjects.Layer();layer.Name='Research_'+old.Name;layer.Color=old.Color
        layer_map[old.Index]=doc.Layers.Add(layer)
    for old in source.Objects:
        attrs=old.Attributes.Duplicate();attrs.LayerIndex=layer_map[old.Attributes.LayerIndex]
        attrs.SetUserString('SceneFlowShadowResearch','20261022')
        assert doc.Objects.Add(old.Geometry,attrs)!=System.Guid.Empty
else:assert all(o.Attributes.GetUserString('SceneFlowShadowResearch')=='20261022' for o in doc.Objects)
view=doc.Views.ActiveView;vp=view.ActiveViewport
vp.SetProjection(DefinedViewportProjection.Perspective,'Shadow_Research',True)
vp.SetCameraLocations(Point3d(11,0,2),Point3d(45,-48,36));vp.ZoomBoundingBox(BoundingBox(Point3d(-11,-7,-2),Point3d(34,7,10)))
width=1024;height=int(round(width*float(vp.Size.Height)/vp.Size.Width))
render_state=doc.RenderSettings.Duplicate();render_hash=int(doc.RenderSettings.Sun.Hash)
sun=doc.RenderSettings.Sun;saved=(sun.Enabled,sun.ManualControlOn,sun.Azimuth,sun.Altitude,doc.Modified,sun.SkylightOn)
report={'pid':EXPECTED_PID,'width':width,'height':height,'captures':[],'warnings':[]}
def api(form):
    result=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='export_shadow_psd',document=int(doc.RuntimeSerialNumber),width=width,path=os.path.join(folder,'current-'+str(form)+'.psd'),overwrite=True,toSun=report['toSun'],includeFormShading=form))))
    assert result['ok'],result
    return result['result']
try:
    sun.BeginChange(Rhino.Render.RenderContent.ChangeContexts.Program)
    try:
        sun.ManualControlOn=True;sun.Azimuth=200;sun.Altitude=40;sun.Enabled=True;sun.SkylightOn=False
    finally:sun.EndChange()
    assert abs(sun.Altitude-40)<1e-6,('Sun altitude was not applied',sun.Altitude)
    report['sunAngles']=[sun.Azimuth,sun.Altitude]
    grid=(vp.ConstructionGridVisible,vp.ConstructionAxesVisible,vp.WorldAxesVisible)
    vp.ConstructionGridVisible=False;vp.ConstructionAxesVisible=False;vp.WorldAxesVisible=False
    vector=sun.Vector;report['toSun']=[-vector.X,-vector.Y,-vector.Z]
    for form in [False,True]:report['current-'+str(form)]=api(form)
    base=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='export_psd',document=int(doc.RuntimeSerialNumber),width=width,path=os.path.join(folder,'base-colors.psd'),overwrite=True))))
    assert base['ok'],base
    report['base']=base['result']
    for scheme in ['SceneLighting','None']:
        mode=DisplayModeDescription.GetDisplayMode(DisplayModeDescription.ShadedId);a=mode.DisplayAttributes
        a.SetFill(Color.White);a.ShadingEnabled=True
        a.UseAssignedObjectMaterial=False;a.UseCustomObjectMaterial=False;a.UseCustomObjectColor=True
        a.ObjectColor=Color.White;a.FrontDiffuse=Color.White;a.FrontOverrideObjectColor=True
        a.FrontMaterialShine=0;a.FrontMaterialTransparency=0;a.BackMaterialShine=0
        a.UseBackfaceMaterial=False;a.UseObjectBackfaceMaterial=False;a.CullBackfaces=False
        a.LightingScheme=System.Enum.Parse(a.GetType().GetProperty('LightingScheme').PropertyType,scheme)
        a.AmbientLightingColor=Color.FromArgb(80,80,80)
        a.ShadowColor=Color.Black;a.ShadowIntensity=100;a.ShadowMemoryUsage=4096
        a.ShadowSoftEdgeQuality=0;a.ShadowEdgeBlur=0;a.ShadowBiasX=1
        a.CustomGroundPlaneOn=False;a.CastShadows=True
        for prop in ['ShowSurfaceEdges','ShowSurfaceEdge','ShowSurfaceNakedEdge','ShowTangentEdges','ShowMeshEdges','ShowEdges','ShowIsoCurves','ShowMeshWires','ShowCurves','ShowPoints','ShowText','ShowAnnotations','ShowLights','DrawGrid','DrawAxes','DrawWorldAxes','DrawGridAxes','ShowWorldAxes']:
            if hasattr(a,prop):setattr(a,prop,False)
        before=(doc.Modified,str(vp.DisplayMode.Id),str(vp.CameraLocation))
        for shadows in [False,True]:
            a.ShadowsOn=shadows
            image=view.CaptureToBitmap(Size(width,height),a);assert image is not None
            name='native-'+scheme+'-'+str(shadows)+'.png';image.Save(os.path.join(folder,name));image.Dispose()
            report['captures'].append(name)
        assert before==(doc.Modified,str(vp.DisplayMode.Id),str(vp.CameraLocation))
    # Re-test the corrected solar transaction independently from the 40-degree comparison.
    sun.BeginChange(Rhino.Render.RenderContent.ChangeContexts.Program)
    try:sun.ManualControlOn=True;sun.Azimuth=135;sun.Altitude=45;sun.Enabled=True
    finally:sun.EndChange()
    assert sun.ManualControlOn and abs(sun.Azimuth-135)<1e-8 and abs(sun.Altitude-45)<1e-8
    vector=sun.Vector;assert abs(vector.Z+math.sqrt(.5))<1e-8
    common=dict(apiVersion=1,operation='export_shadow_psd',document=int(doc.RuntimeSerialNumber),width=128,overwrite=True)
    auto=json.loads(McpApi.Execute(json.dumps(dict(common,path=os.path.join(folder,'verified-sun-45-auto.psd')))))
    explicit=json.loads(McpApi.Execute(json.dumps(dict(common,path=os.path.join(folder,'verified-sun-45-explicit.psd'),toSun=[-vector.X,-vector.Y,-vector.Z]))))
    assert auto['ok'] and explicit['ok'] and auto['result']['lightSource']=='rhino_sun'
    with open(auto['result']['export']['path'],'rb') as f:reference=f.read()
    with open(explicit['result']['export']['path'],'rb') as f:assert f.read()==reference
    report['sunTest']=dict(ok=True,altitude=sun.Altitude,azimuth=sun.Azimuth,vector=[vector.X,vector.Y,vector.Z],samePsdBytes=True)
finally:
    doc.RenderSettings=render_state
    assert int(doc.RenderSettings.Sun.Hash)==render_hash,'Render settings not restored'
    render_state.Dispose()
    if 'grid' in locals():vp.ConstructionGridVisible=grid[0];vp.ConstructionAxesVisible=grid[1];vp.WorldAxesVisible=grid[2]
    doc.Modified=saved[4]
report['sunTest']['renderSettingsRestored']=True
with open(os.path.join(folder,'verified-sun-45.json'),'w') as f:json.dump(report['sunTest'],f,indent=2)
report['complete']=True
with open(os.path.join(folder,'native-report.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
