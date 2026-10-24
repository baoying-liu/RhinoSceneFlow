using RhinoSceneFlow.Core;

static void Check(bool condition, string message)
{ if (!condition) throw new Exception(message); }
static ClipVertex V(double x, double y, double z = .6, double w = 1) => new(x, y, z, w);
static IEnumerable<Triangle> Quad(int group, double z, double left = -.8, double right = .8)
{
    yield return new(V(left, -.8, z), V(right, -.8, z), V(right, .8, z), group);
    yield return new(V(left, -.8, z), V(right, .8, z), V(left, .8, z), group);
}
var groups = new[] {
    new ColorGroup("#E65032 建筑 / 墙面", new Rgb(230, 80, 50)),
    new ColorGroup("#3282C8 铺装", new Rgb(50, 130, 200)),
    new ColorGroup("hidden", new Rgb(0, 255, 0))
};
var geometry = Quad(1, .7).Concat(Quad(0, .2, -.3, .3)).Concat(Quad(2, .9)).ToArray();
var image = FlatRasterizer.Render(96, 64, groups, geometry);
Check(image.SampleOwner(48, 32, 0) == 0, "Foreground must occlude background.");
Check(image.SampleOwner(15, 32, 0) == 1, "Exposed background must remain.");
Check(image.CompositeChannel(3, 0, 0) == 0, "Background must be transparent.");
Check(image.GetVisibleLayers().Count == 2, "Fully occluded groups must not create layers.");
var reverse = FlatRasterizer.Render(96, 64, groups, Enumerable.Reverse(geometry));
for (int y = 0; y < 64; y++) for (int x = 0; x < 96; x++) for (int s = 0; s < 4; s++)
    Check(image.SampleOwner(x, y, s) == reverse.SampleOwner(x, y, s), "Depth must be independent of draw order.");

var cut = FlatRasterizer.Render(32, 32, groups, [new(V(-2, -.5, -.5), V(.8, -.5, .5), V(0, .8, .5), 0)]);
Check(cut.GetVisibleLayers().Count == 1, "Near/side-plane crossing triangles must be clipped, not discarded.");
var behind = FlatRasterizer.Render(32, 32, groups, [new(V(-.5, -.5, -.2), V(.5, -.5, -.2), V(0, .5, -.2), 0)]);
Check(behind.GetVisibleLayers().Count == 0, "Geometry behind near plane must be excluded.");
var perspective = new CameraProjection(new(0, 0, 0), new(1, 0, 0), new(0, 1, 0), new(0, 0, 1), -1, 1, -1, 1, 1, 100, false);
Check(Math.Abs(perspective.Project(new(0, 0, -1)).Z) < 1e-10, "Perspective near plane.");
var far = perspective.Project(new(0, 0, -100));
Check(Math.Abs(far.Z / far.W - 1) < 1e-10, "Perspective far plane.");
Check(Math.Abs(perspective.Project(new(2, 0, -2)).X / 2 - 1) < 1e-10, "Perspective frustum edge.");

// Fractional coverage across adjacent groups must reconstruct the supersampled composite.
var diagonal = FlatRasterizer.Render(97, 65, groups,
    Quad(1, .8, -1, 1).Concat([new Triangle(V(-.9, -.7, .2), V(.9, -.4, .2), V(-.4, .9, .2), 0)]));
for (int y = 0; y < diagonal.Height; y++) for (int x = 0; x < diagonal.Width; x++)
{
    double alpha = 0; var premul = new double[3];
    for (int g = groups.Length - 1; g >= 0; g--)
    {
        double a = diagonal.LayerAlpha(g, x, y) / 255.0;
        var color = groups[g].Color;
        byte[] channels = [color.R, color.G, color.B];
        for (int c = 0; c < 3; c++) premul[c] = channels[c] * a + premul[c] * (1 - a);
        alpha = a + alpha * (1 - a);
    }
    Check(Math.Abs(alpha * 255 - diagonal.CompositeChannel(3, x, y)) <= 1.1, "Composite alpha mismatch.");
    if (alpha > 0) for (int c = 0; c < 3; c++)
        Check(Math.Abs(premul[c] / alpha - diagonal.CompositeChannel(c, x, y)) <= 1.1, "Composite color mismatch.");
}

string output = Path.GetFullPath(args.Length > 0 ? args[0] : "artifacts/validation");
Directory.CreateDirectory(output);
Check(PsdWriter.Save(Path.Combine(output, "occlusion.psd"), image) == 2, "PSD visible layer count.");
PsdWriter.Save(Path.Combine(output, "antialias.psd"), diagonal);
// An independent decoder compares against this reference, not against our PSD reader.
using (var raw = File.Create(Path.Combine(output, "antialias.rgba")))
    for (int y = 0; y < diagonal.Height; y++) for (int x = 0; x < diagonal.Width; x++)
        for (int c = 0; c < 4; c++) raw.WriteByte(diagonal.CompositeChannel(c, x, y));
byte[] original = File.ReadAllBytes(Path.Combine(output, "occlusion.psd"));
using var canceled = new CancellationTokenSource(); canceled.Cancel();
try { PsdWriter.Save(Path.Combine(output, "occlusion.psd"), image, canceled.Token); throw new Exception("Cancellation ignored."); }
catch (OperationCanceledException) { }
Check(original.SequenceEqual(File.ReadAllBytes(Path.Combine(output, "occlusion.psd"))), "Cancellation must preserve existing output.");
try { PsdWriter.Save(Path.Combine(output, "occlusion.psd"), image, overwrite: false); throw new Exception("Overwrite protection ignored."); }
catch (IOException) { }
Check(original.SequenceEqual(File.ReadAllBytes(Path.Combine(output, "occlusion.psd"))), "Refusing overwrite must preserve existing output.");
Console.WriteLine($"PASS: occlusion, clipping, projection, alpha composition, PSD export, cancellation. Fixtures: {output}");

// Analytic shadow: a plate at z=2, lit from +X/+Z, casts [-3,-1] onto z=0.
static WorldTriangle[] Plate(double z, double radius) => [
    new(new(-radius,-radius,z),new(radius,-radius,z),new(radius,radius,z)),
    new(new(-radius,-radius,z),new(radius,radius,z),new(-radius,radius,z))];
var shadowCamera = new CameraProjection(new(0,0,10),new(1,0,0),new(0,1,0),new(0,0,1),-5,5,-5,5,.1,20,true);
var shadowScene = Plate(0,5).Concat(Plate(2,1)).ToArray();
var shadow = ShadowRenderer.Render(100,100,shadowCamera,shadowScene,new(new(1,0,1),new(90,90,90)));
Check(shadow.CompositeChannel(3,30,50)==255,"Analytic projected shadow missing.");
Check(shadow.CompositeChannel(3,50,50)==0,"Lit plate must occlude its ground shadow.");
Check(shadow.CompositeChannel(3,80,50)==0,"Unshadowed ground must be transparent.");
var softAlpha = ShadowRenderer.Render(100,100,shadowCamera,shadowScene,new(new(1,0,1),new(12,34,56),Opacity:.5));
Check(softAlpha.LayerAlpha(0,30,50)==128,"Shadow opacity must affect pixel layer alpha.");
var below = ShadowRenderer.Render(32,32,shadowCamera,Plate(0,5),new(new(0,0,-1),new(90,90,90)));
Check(below.GetVisibleLayers().Count==0,"Backlighting must not accidentally become cast shadow.");
var form = ShadowRenderer.Render(32,32,shadowCamera,Plate(0,5),new(new(0,0,-1),new(90,90,90),true));
Check(form.CompositeChannel(3,16,16)==255,"Optional form shading missing.");
PsdWriter.Save(Path.Combine(output,"shadow.psd"),shadow);
PsdWriter.Save(Path.Combine(output,"shadow-opacity.psd"),softAlpha);
PsdWriter.Save(Path.Combine(output,"shadow-empty.psd"),below,allowEmpty:true);
// Perspective projection has the same shadow point; test unprojection away from the optical axis.
var pc = shadowCamera with { Parallel=false, Left=-.05, RightEdge=.05, Bottom=-.05, Top=.05 };
var ps = ShadowRenderer.Render(100,100,pc,shadowScene,new(new(1,0,1),new(90,90,90)));
Check(ps.CompositeChannel(3,30,50)==255 && ps.CompositeChannel(3,50,50)==0,"Perspective shadow projection.");
// Translation invariance at survey-scale offsets.
var offset = new Vec3(1e8,-1e8,1e8);
var shifted = ShadowRenderer.Render(100,100,shadowCamera with { Origin=shadowCamera.Origin+offset },
    shadowScene.Select(t=>new WorldTriangle(t.A+offset,t.B+offset,t.C+offset)).ToArray(),new(new(1,0,1),new(90,90,90)));
for(int y=0;y<100;y++) for(int x=0;x<100;x++)
    Check(shifted.CompositeChannel(3,x,y)==shadow.CompositeChannel(3,x,y),"Large-coordinate shadow must be translation invariant.");
Console.WriteLine("PASS: analytic shadows, visibility, perspective, opacity, optional form shading, empty PSD, large coordinates.");

var offscreen = Plate(0,5).Concat(Plate(12,1).Select(t=> new WorldTriangle(t.A+new Vec3(8,0,0),t.B+new Vec3(8,0,0),t.C+new Vec3(8,0,0)))).ToArray();
var outside = ShadowRenderer.Render(100,100,shadowCamera,offscreen,new(new(1,0,1),new(90,90,90)));
Check(outside.CompositeChannel(3,10,50)==255,"A caster outside the camera frustum must still cast shadows.");
Console.WriteLine("PASS: off-camera casters.");

var sn = new Vec3(-.9,0,.1).Unit;
var smoothPlane = Plate(0,5).Select(t=>t with { NA=sn,NB=sn,NC=sn }).ToArray();
var smoothForm = ShadowRenderer.Render(32,32,shadowCamera,smoothPlane,new(new(1,0,1),new(90,90,90),true));
Check(smoothForm.CompositeChannel(3,16,16)==255,"Smooth receiver normals must control form shading, independently of triangulation.");
Console.WriteLine("PASS: interpolated receiver normals.");

// A smooth convex sphere has no cast shadows of its own. Coarse mesh facets must
// not turn its smooth-normal terminator into a noisy ring of false occlusion.
var ball = new List<WorldTriangle>();
Vec3 BallPoint(int latitude,int longitude) => new(3*Math.Sin(latitude*Math.PI/16)*Math.Cos(longitude*Math.PI/16),
    3*Math.Sin(latitude*Math.PI/16)*Math.Sin(longitude*Math.PI/16),3*Math.Cos(latitude*Math.PI/16));
void AddBall(Vec3 a,Vec3 b,Vec3 c) => ball.Add(new(a,b,c,a.Unit,b.Unit,c.Unit));
for(int j=0;j<16;j++) for(int i=0;i<32;i++)
{
    var a=BallPoint(j,i);var b=BallPoint(j,i+1);var c=BallPoint(j+1,i+1);var d=BallPoint(j+1,i);
    AddBall(a,b,c);AddBall(a,c,d);
}
var sphereShadow=ShadowRenderer.Render(128,128,shadowCamera,ball,new(new(1,0,1),new(90,90,90)));
Check(sphereShadow.GetVisibleLayers().Count==0,"A convex smooth sphere must not generate faceted shadow acne.");
Console.WriteLine("PASS: smooth sphere terminator has no false cast-shadow pixels.");

// Independent backend comparison: the ray reference has geometric normals only,
// so it cannot use the known tangent-plane displacement heuristic.
var volumeSettings=new ShadowSettings(new(1,0,1),new(90,90,90));
void CompareVolume(string name,CameraProjection cam,IReadOnlyList<WorldTriangle> scene)
{
    var geometric=scene.Select(t=>t with { NA=null,NB=null,NC=null }).ToArray();
    var reference=ShadowRenderer.Render(96,96,cam,geometric,volumeSettings);
    var actual=ShadowVolumeRenderer.Render(96,96,cam,scene,volumeSettings);
    int differences=0,interiorDifferences=0;
    for(int y=0;y<96;y++)for(int x=0;x<96;x++)for(int sample=0;sample<4;sample++)
        if(reference.SampleOwner(x,y,sample)!=actual.SampleOwner(x,y,sample))
        {
            differences++;
            bool edge=false;int owner=reference.SampleOwner(x,y,sample);
            for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++)for(int ss=0;ss<4;ss++)
                if(x+dx>=0&&x+dx<96&&y+dy>=0&&y+dy<96&&reference.SampleOwner(x+dx,y+dy,ss)!=owner)edge=true;
            if(!edge){interiorDifferences++;if(interiorDifferences<12)Console.WriteLine($"Interior {name}: {x},{y}/{sample}: ray={owner},volume={actual.SampleOwner(x,y,sample)}");}
        }
    Check(interiorDifferences==0,$"Volume/ray interior visibility mismatch: {name}: {interiorDifferences}/{differences}");
    Console.WriteLine($"Volume oracle {name}: {differences} edge sample differences, {interiorDifferences} interior differences.");
    PsdWriter.Save(Path.Combine(output,$"volume-{name}.psd"),actual,allowEmpty:true);
}
CompareVolume("plate",shadowCamera,shadowScene);
CompareVolume("perspective",pc,shadowScene);
CompareVolume("offscreen",shadowCamera,offscreen);
CompareVolume("sphere",shadowCamera,ball.Concat(Plate(-3.2,5)).ToArray());
// A receiver lies in the shadow volume and the closing cap is beyond camera.Far.
CompareVolume("far-cap",shadowCamera with { Far=10.5 },shadowScene);
CompareVolume("near-crossing",pc with { Origin=new(-1.5,0,1), Near=.2, Left=-.3,RightEdge=.3,Bottom=-.3,Top=.3 },shadowScene);
var gapReceiver=Plate(0,2).Select(t=>t with { NA=new Vec3(-.3,-.3,1).Unit,NB=new Vec3(.3,-.3,1).Unit,NC=new Vec3(.3,.3,1).Unit });
var gapRoof=new[]{new WorldTriangle(new(.15,-.5,.25),new(.35,-.5,.25),new(.35,.5,.25)),new WorldTriangle(new(.15,-.5,.25),new(.35,.5,.25),new(.15,.5,.25))};
var gapScene=gapReceiver.Concat(gapRoof).ToArray();
var gapVolume=ShadowVolumeRenderer.Render(100,100,shadowCamera with { Left=-2,RightEdge=2,Bottom=-2,Top=2 },gapScene,volumeSettings);
Check(gapVolume.CompositeChannel(3,50,50)==255,"Volume must preserve the known smooth-normal gap shadow.");
CompareVolume("gap",shadowCamera with { Left=-2,RightEdge=2,Bottom=-2,Top=2 },gapScene);
CompareVolume("reverse-winding",shadowCamera,shadowScene.Select(t=>new WorldTriangle(t.C,t.B,t.A)).ToArray());
CompareVolume("overlapping",shadowCamera,shadowScene.Concat(Plate(3,.7)).ToArray());
var volumeShift=ShadowVolumeRenderer.Render(100,100,shadowCamera with { Origin=shadowCamera.Origin+offset },
 shadowScene.Select(t=>new WorldTriangle(t.A+offset,t.B+offset,t.C+offset)).ToArray(),volumeSettings);
var volumeOriginal=ShadowVolumeRenderer.Render(100,100,shadowCamera,shadowScene,volumeSettings);
for(int y=0;y<100;y++)for(int x=0;x<100;x++)Check(volumeShift.CompositeChannel(3,x,y)==volumeOriginal.CompositeChannel(3,x,y),"Volume survey coordinate invariance.");
Console.WriteLine("PASS: shadow volumes vs geometric-ray oracle, gap regression, perspective, clipping, far caps, overlap, winding, sphere, large coordinates.");

var emptyVolume=ShadowVolumeRenderer.Render(32,32,shadowCamera,Plate(0,5),new(new(0,0,-1),new(90,90,90)));
Check(emptyVolume.GetVisibleLayers().Count==0,"Volume backlighting must remain optional.");
var formVolume=ShadowVolumeRenderer.Render(32,32,shadowCamera,smoothPlane,new(new(1,0,1),new(90,90,90),true));
Check(formVolume.CompositeChannel(3,16,16)==255,"Volume form shading must use smooth normals.");
var styledVolume=ShadowVolumeRenderer.Render(100,100,shadowCamera,shadowScene,volumeSettings with { Opacity=.5 });
Check(styledVolume.LayerAlpha(0,30,50)==128,"Volume opacity.");
using var volumeCanceled=new CancellationTokenSource();volumeCanceled.Cancel();
try { ShadowVolumeRenderer.Render(32,32,shadowCamera,shadowScene,volumeSettings,volumeCanceled.Token);throw new Exception("Volume cancellation ignored."); }
catch(OperationCanceledException) { }
Console.WriteLine("PASS: volume style, optional smooth form shading, empty mask and cancellation.");

// Surface refinement must be able to remove false faceted occlusion without any
// displacement, while retaining an independently known thin projected shadow.
int surfaceQueries=0;
var refinedGap=ShadowVolumeRenderer.Render(100,100,shadowCamera with { Left=-2,RightEdge=2,Bottom=-2,Top=2 },
 gapScene,volumeSettings,refineSurface:(sx,sy)=>
 {
     surfaceQueries++;
     double worldX=-2+(sx+.5)/200*4,worldY=2-(sy+.5)/200*4;
     return worldX>-.1&&worldX<.1&&worldY>-.5&&worldY<.5;
 });
Check(surfaceQueries>0 && refinedGap.CompositeChannel(3,50,50)==255,"Surface refinement must preserve the gap shadow.");
Check(refinedGap.CompositeChannel(3,60,50)==0,"Surface refinement must keep lit receivers clear.");
int sphereQueries=0;
var refinedSphere=ShadowVolumeRenderer.Render(96,96,shadowCamera,ball,volumeSettings,
 refineSurface:(_,_)=>{sphereQueries++;return false;});
Check(sphereQueries>0&&refinedSphere.GetVisibleLayers().Count==0,"A convex exact sphere has no cast shadows of its own.");
Console.WriteLine("PASS: source-surface refinement preserves analytic gap shadows and convex-sphere visibility.");

// Direct sunlight includes a convex sphere's backlit side even though it has no
// cast shadow of its own. Its analytic terminator must remain independent of facets.
var directSettings=volumeSettings with { IncludeFormShading=true };
bool AnalyticBall(int sx,int sy)
{
    var a=shadowCamera.At((sx+.5)/192,1-(sy+.5)/192,shadowCamera.Near);
    var b=shadowCamera.At((sx+.5)/192,1-(sy+.5)/192,shadowCamera.Far);
    var d=(b-a).Unit;double q=a.Dot(d),disc=q*q-a.Dot(a)+9;
    if(disc<0)return false;
    double distance=-q-Math.Sqrt(disc);if(distance<0)return false;
    return (a+d*distance).Unit.Dot(directSettings.ToSun.Unit)<=1e-10;
}
var directBall=ShadowVolumeRenderer.Render(96,96,shadowCamera,ball,directSettings,refineSurface:AnalyticBall);
int directDark=0,directLit=0;
for(int y=0;y<96;y++)for(int x=0;x<96;x++)for(int s=0;s<4;s++)
{
    var a=shadowCamera.At((x+(s%2==0?.25:.75))/96,1-(y+(s<2?.25:.75))/96,shadowCamera.Near);
    // Avoid mesh silhouette approximation in this test; test the body and terminator.
    if(a.X*a.X+a.Y*a.Y>6.25)continue;
    bool expected=AnalyticBall(x*2+s%2,y*2+s/2);
    Check((directBall.SampleOwner(x,y,s)==0)==expected,"Direct sphere form shadow differs from analytic sunlight.");
    if(expected)directDark++;else directLit++;
}
Check(directDark>0&&directLit>0,"Direct sphere must contain both lit and backlit samples.");
Console.WriteLine("PASS: direct sunlight analytic sphere body and terminator, without reflections.");

// Separate passes overlap in the PSD; their composite must match normal alpha blending.
var batchMaterial=FlatRasterizer.Render(100,100,[new ColorGroup("Material #C86432",new(200,100,50))],
 shadowScene.Select(t=>new Triangle(shadowCamera.Project(t.A),shadowCamera.Project(t.B),shadowCamera.Project(t.C),0)));
var stack=new LayerStack(softAlpha,batchMaterial);
Check(stack.Groups.Count==2 && stack.Groups[0].Name=="Shadow","Shadow pass must be above material.");
Check(stack.CompositeChannel(3,30,50)==255,"Material keeps the composite opaque beneath shadow.");
Check(stack.CompositeChannel(0,30,50)==106 && stack.CompositeChannel(1,30,50)==67,"Independent shadow opacity composition.");
PsdWriter.Save(Path.Combine(output,"batch-stack.psd"),stack);
var emptyPass=new LayerStack(ShadowVolumeRenderer.Render(100,100,shadowCamera,Plate(0,5),new(new(0,0,-1),new(90,90,90))),batchMaterial);
Check(emptyPass.GetVisibleLayers().Count==2,"A selected empty Shadow pass must remain editable in the PSD.");
PsdWriter.Save(Path.Combine(output,"batch-empty-shadow.psd"),emptyPass);
string namesDirectory=Path.Combine(output,"names-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(namesDirectory);
File.WriteAllText(Path.Combine(namesDirectory,"视图.psd"),"existing");
File.WriteAllText(Path.Combine(namesDirectory,"视图001.psd"),"existing");
var reserved=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
var numbered=OutputNames.Reserve(namesDirectory,"视图",reserved,_=>FileCollision.Number);
Check(Path.GetFileName(numbered.Path)=="视图002.psd"&&!numbered.Overwrite,"Numbering must skip existing suffixes.");
var next=OutputNames.Reserve(namesDirectory,"视图",reserved,_=>FileCollision.Number);
Check(Path.GetFileName(next.Path)=="视图003.psd","Numbering must reserve names within a batch.");
var overwritten=OutputNames.Reserve(namesDirectory,"视图",new HashSet<string>(),_=>FileCollision.Overwrite);
Check(overwritten.Overwrite&&Path.GetFileName(overwritten.Path)=="视图.psd","Explicit overwrite policy.");
try{OutputNames.Reserve(namesDirectory,"视图",new HashSet<string>(),_=>FileCollision.Cancel);throw new Exception("Collision cancellation ignored.");}
catch(OperationCanceledException){}
var same=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
var aName=OutputNames.Reserve(namesDirectory,"a/b",same,_=>FileCollision.Overwrite);
var bName=OutputNames.Reserve(namesDirectory,"a:b",same,_=>FileCollision.Overwrite);
Check(aName.Path!=bName.Path&&!bName.Overwrite,"Sanitized duplicate names must never overwrite another planned view.");
Check(OutputNames.SafeStem("CON")=="_CON"&&OutputNames.SafeStem("..")!="..","Invalid/device filenames.");
Console.WriteLine("PASS: multi-pass PSD composition, empty channels, Unicode filenames, suffix reservation, overwrite and cancellation.");

string stage=Directory.CreateTempSubdirectory("SceneFlow-validation-").FullName;
try
{
    using var pixels=new DiskPassImage(stage,96,64,[new("RGB capture",new(0,0,0))],true);
    for(int y=0;y<64;y++)
    {
        var row=new byte[96*4];for(int x=0;x<96;x++){row[x*4]=(byte)(x*2);row[x*4+1]=(byte)(y*3);row[x*4+2]=100;row[x*4+3]=(byte)(x<30?128:255);}pixels.WriteRgbaRow(y,0,row);
    }
    using var stored=new DiskPassImage(stage,96,64,groups);
    stored.WriteTile(0,0,image);
    for(int y=0;y<64;y++)for(int x=0;x<96;x++)for(int c=0;c<4;c++)
        Check(stored.CompositeChannel(c,x,y)==image.CompositeChannel(c,x,y),"Disk staging changed a channel.");
    foreach(string blend in ConfiguredStack.BlendKeys)
    {
        var configured=new ConfiguredStack(new("RGB capture",pixels,blend,153),new("Materials",stored,"norm",255,true));
        PsdWriter.Save(Path.Combine(output,"configured-"+blend.Trim()+".psd"),configured);
    }
    var folderBlend=new ConfiguredStack(new("Materials",stored,"mul ",128,true),new("RGB capture",pixels));
    PsdWriter.Save(Path.Combine(output,"configured-folder.psd"),folderBlend);
    var cropped=new ImageWindow(image,20,10,40,30);
    Check(cropped.CompositeChannel(0,5,5)==image.CompositeChannel(0,25,15),"Crop must preserve source pixel coordinates.");
    try{new ConfiguredStack(new StyledPass("Invalid",pixels,"invalid"));throw new Exception("Invalid PSD blend accepted.");}catch(ArgumentException){}
}
finally{Directory.Delete(stage,true);}
Console.WriteLine("PASS: RGB disk staging, grouped PSD blend metadata, opacity and crop coordinates.");

if(args.Contains("--large"))
{
    string largeStage=Directory.CreateTempSubdirectory("SceneFlow-8K-").FullName;
    try
    {
        using var large=new DiskPassImage(largeStage,8192,2048,[new("8K RGB",new(0,0,0))],true);
        var row=new byte[8192*4];for(int x=0;x<8192;x++){row[x*4]=(byte)(x%256);row[x*4+1]=110;row[x*4+2]=180;row[x*4+3]=255;}
        for(int y=0;y<2048;y++)large.WriteRgbaRow(y,0,row);
        PsdWriter.Save(Path.Combine(output,"large-8k.psd"),new ConfiguredStack(new StyledPass("8K RGB",large)));
        Console.WriteLine("PASS: 8192 x 2048 row-streamed PSD, beyond the old 8 million pixel limit.");
    }
    finally{Directory.Delete(largeStage,true);}
}
