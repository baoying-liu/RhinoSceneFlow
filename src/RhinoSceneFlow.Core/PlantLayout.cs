namespace RhinoSceneFlow.Core;

public sealed class PlantPaletteItem
{
    public Guid Asset {get;set;}
    public double Weight {get;set;}=1;
    public double SpacingMeters {get;set;}=1;
}
public sealed class PlantLayoutSettings
{
    public double Density {get;set;}=.2; // plants / square metre, including manually planted specimens
    public int LayoutSeed {get;set;}=42;
    public int SizeSeed {get;set;}=43;
    public int MirrorSeed {get;set;}=44;
    public double MinScale {get;set;}=.75;
    public double MaxScale {get;set;}=1.5;
    public double MinSliderLow {get;set;}=.5;
    public double MinSliderHigh {get;set;}=1;
    public double MaxSliderLow {get;set;}=1;
    public double MaxSliderHigh {get;set;}=2;
    public bool Mirror {get;set;}=true;
    public bool OverrideSpacing {get;set;}
    public double EdgeDistance {get;set;}=1;
    public double EdgeStrength {get;set;}
    public double[] EdgeCurve {get;set;}=[0,.25,.5,.75,1];
    public bool EdgeDensity {get;set;}=true;
    public bool EdgeSize {get;set;}=true;
    public void Validate()
    {
        if(!double.IsFinite(Density)||Density<0||Density>1000||!double.IsFinite(MinScale)||!double.IsFinite(MaxScale)||MinScale<=0||MaxScale<MinScale||MaxScale>100||
            new[]{MinSliderLow,MinSliderHigh,MaxSliderLow,MaxSliderHigh}.Any(v=>!double.IsFinite(v)||v<=0||v>100)||MinSliderLow>=MinSliderHigh||MaxSliderLow>=MaxSliderHigh||MinScale<MinSliderLow||MinScale>MinSliderHigh||MaxScale<MaxSliderLow||MaxScale>MaxSliderHigh||
            !double.IsFinite(EdgeDistance)||EdgeDistance<0||EdgeDistance>10000||!double.IsFinite(EdgeStrength)||EdgeStrength<0||EdgeStrength>1||EdgeCurve.Length!=5||EdgeCurve.Any(v=>!double.IsFinite(v)||v<0||v>1))throw new ArgumentException("种植密度、比例、滑块区间或边缘曲线无效。");
    }
    public double EdgeFactor(double distance)
    {
        if(EdgeStrength==0||EdgeDistance==0)return 1;
        double x=Math.Clamp(distance/EdgeDistance,0,1)*4;int i=Math.Min(3,(int)x);double value=EdgeCurve[i]+(EdgeCurve[i+1]-EdgeCurve[i])*(x-i);
        return 1-EdgeStrength+EdgeStrength*value;
    }
}
public sealed record LayoutTriangle(Vec3 A,Vec3 B,Vec3 C);
public sealed record LayoutEdge(Vec3 A,Vec3 B);
public sealed record LayoutManual(string Id,Guid Asset,Vec3 Position,bool Detached=false,double? CustomScale=null,bool? CustomMirror=null,double? SpacingMeters=null);
public sealed record LayoutPlant(string Id,Guid Asset,Vec3 Position,bool Manual,double Scale,bool Mirror,bool Detached=false);
public sealed record PlantLayoutResult(LayoutPlant[] Plants,int Target,int Attempts,bool Limited,double Area,int ExclusionConflicts=0);

/// <summary>Owned metre-space snapshots only. Stable streams for layout, scale and mirror.</summary>
public static class PlantLayout
{
    private static ulong Hash(string id,int seed)
    {
        ulong h=14695981039346656037UL^(uint)seed;foreach(char c in id){h^=c;h*=1099511628211UL;}h^=h>>30;h*=0xbf58476d1ce4e5b9UL;h^=h>>27;h*=0x94d049bb133111ebUL;return h^(h>>31);
    }
    public static double Random(string id,int seed)=>(Hash(id,seed)>>11)*(1.0/(1UL<<53));
    public static PlantLayoutResult Generate(LayoutTriangle[] triangles,LayoutEdge[] edges,PlantPaletteItem[] palette,LayoutManual[] manual,PlantLayoutSettings settings,CancellationToken cancel=default,IReadOnlySet<string>? excluded=null,PlantExclusions? exclusions=null)
    {
        settings.Validate();if(palette.Length is <1 or >64||palette.Any(p=>p.Asset==Guid.Empty||!double.IsFinite(p.Weight)||p.Weight<=0||!double.IsFinite(p.SpacingMeters)||p.SpacingMeters<0||p.SpacingMeters>1000)||palette.Select(p=>p.Asset).Distinct().Count()!=palette.Length)throw new ArgumentException("植物组合需为 1–64 种，间距和比重必须有效。");
        if(manual.Length>10000||triangles.Length>2_000_000||edges.Length>200000)throw new ArgumentException("种植快照过大。");
        var weights=new double[palette.Length];double totalWeight=0;for(int i=0;i<palette.Length;i++)weights[i]=totalWeight+=palette[i].Weight;
        var cumulative=new double[triangles.Length];double area=0;for(int i=0;i<triangles.Length;i++){var t=triangles[i];double a=(t.B-t.A).Cross(t.C-t.A).Length*.5;if(!double.IsFinite(a))throw new ArgumentException("曲面坐标无效。");cumulative[i]=area+=a;}
        double desired=area*settings.Density;if(!double.IsFinite(desired)||desired>10000)throw new ArgumentException("当前面积和密度超过 10000 株，请降低密度。");int target=(int)Math.Round(desired);
        if(manual.Any(m=>m.SpacingMeters is double spacing&&(!double.IsFinite(spacing)||spacing<0||spacing>1000)))throw new ArgumentException("自定义植物间距无效。");
        var result=new List<LayoutPlant>();double cell=Math.Max(.001,Math.Max(palette.Max(p=>p.SpacingMeters),manual.Select(m=>m.SpacingMeters??0).DefaultIfEmpty().Max()));var cells=new Dictionary<(long,long,long),List<(Vec3 P,double S)>>();
        (long X,long Y,long Z) Key(Vec3 p)=>((long)Math.Floor(p.X/cell),(long)Math.Floor(p.Y/cell),(long)Math.Floor(p.Z/cell));
        void AddCell(Vec3 p,double spacing){var k=Key(p);if(!cells.TryGetValue(k,out var values))cells[k]=values=[];values.Add((p,spacing));}
        var boundary=settings.EdgeStrength>0&&edges.Length>0?new EdgeTree(edges,cancel):null;
        double Edge(Vec3 p)=>boundary==null?1:settings.EdgeFactor(boundary.Distance(p,settings.EdgeDistance));
        LayoutPlant Make(string id,Guid asset,Vec3 p,bool hand,bool detached,double edge)=>new(id,asset,p,hand,(settings.MinScale+Random(id,settings.SizeSeed)*(settings.MaxScale-settings.MinScale))*(settings.EdgeSize?Math.Max(.01,edge):1),settings.Mirror&&Random(id,settings.MirrorSeed)<.5,detached);
        foreach(var m in manual)
        {
            cancel.ThrowIfCancellationRequested();var entry=palette.FirstOrDefault(p=>p.Asset==m.Asset);if(entry==null&&m.CustomScale==null)throw new ArgumentException("手工植物仍引用已移除的组合项，请先保留该项或移除对应手工植物。");
            if(m.CustomScale is double cs&&(!double.IsFinite(cs)||cs<=0||cs>100))throw new ArgumentException("自定义植物比例无效。");
            var row=Make(m.Id,m.Asset,m.Position,true,m.Detached,Edge(m.Position));result.Add(row with{Scale=m.CustomScale??row.Scale,Mirror=m.CustomMirror??row.Mirror});AddCell(m.Position,entry?.SpacingMeters??m.SpacingMeters??palette.Max(p=>p.SpacingMeters));
        }
        var random=new System.Random(settings.LayoutSeed);int attempts=0,maxAttempts=Math.Min(500_000,Math.Max(1000,target*150));
        while(result.Count<target&&area>0&&attempts<maxAttempts)
        {
            cancel.ThrowIfCancellationRequested();int attempt=attempts++;double pick=random.NextDouble()*area;int ti=Array.BinarySearch(cumulative,pick);if(ti<0)ti=~ti;ti=Math.Min(ti,triangles.Length-1);
            double u=Math.Sqrt(random.NextDouble()),v=random.NextDouble();var t=triangles[ti];var p=t.A+(t.B-t.A)*(u*(1-v))+(t.C-t.A)*(u*v);
            int pi=Array.BinarySearch(weights,random.NextDouble()*totalWeight);if(pi<0)pi=~pi;pi=Math.Min(pi,palette.Length-1);var entry=palette[pi];double edge=Edge(p);
            if(settings.EdgeDensity&&random.NextDouble()>edge)continue;
            if(exclusions?.Contains(p)==true)continue;
            bool valid=true;if(!settings.OverrideSpacing){var k=Key(p);for(int x=-1;x<=1&&valid;x++)for(int y=-1;y<=1&&valid;y++)for(int z=-1;z<=1&&valid;z++)if(cells.TryGetValue((k.X+x,k.Y+y,k.Z+z),out var near))foreach(var other in near)if((p-other.P).Length<(entry.SpacingMeters+other.S)*.5){valid=false;break;}}
            if(!valid)continue;string id="auto:"+attempt;if(excluded?.Contains(id)==true)continue;result.Add(Make(id,entry.Asset,p,false,false,edge));AddCell(p,entry.SpacingMeters);
        }
        return new(result.ToArray(),target,attempts,result.Count<target,area,manual.Count(m=>exclusions?.Contains(m.Position)==true));
    }

    // Bounding tree avoids scanning every boundary segment for every rejected candidate.
    private sealed class EdgeTree
    {
        private sealed record Node(Vec3 Min,Vec3 Max,int Start,int Count,Node? Left=null,Node? Right=null);
        private readonly LayoutEdge[] edges;private readonly Node root;
        private static double Axis(Vec3 v,int axis)=>axis==0?v.X:axis==1?v.Y:v.Z;
        internal EdgeTree(LayoutEdge[] source,CancellationToken cancel){edges=(LayoutEdge[])source.Clone();root=Build(0,edges.Length,cancel);}
        private Node Build(int start,int count,CancellationToken cancel)
        {
            cancel.ThrowIfCancellationRequested();double x=double.PositiveInfinity,y=x,z=x,xx=double.NegativeInfinity,yy=xx,zz=xx;
            for(int i=start;i<start+count;i++)foreach(var p in new[]{edges[i].A,edges[i].B}){x=Math.Min(x,p.X);y=Math.Min(y,p.Y);z=Math.Min(z,p.Z);xx=Math.Max(xx,p.X);yy=Math.Max(yy,p.Y);zz=Math.Max(zz,p.Z);}
            var min=new Vec3(x,y,z);var max=new Vec3(xx,yy,zz);if(count<=12)return new(min,max,start,count);
            int axis=xx-x>=yy-y&&xx-x>=zz-z?0:yy-y>=zz-z?1:2;Array.Sort(edges,start,count,Comparer<LayoutEdge>.Create((a,b)=>(Axis(a.A,axis)+Axis(a.B,axis)).CompareTo(Axis(b.A,axis)+Axis(b.B,axis))));int half=count/2;
            return new(min,max,start,count,Build(start,half,cancel),Build(start+half,count-half,cancel));
        }
        internal double Distance(Vec3 p,double maximum)
        {
            double best=maximum*maximum;
            double Bound(Node n){double x=Math.Max(0,Math.Max(n.Min.X-p.X,p.X-n.Max.X)),y=Math.Max(0,Math.Max(n.Min.Y-p.Y,p.Y-n.Max.Y)),z=Math.Max(0,Math.Max(n.Min.Z-p.Z,p.Z-n.Max.Z));return x*x+y*y+z*z;}
            void Visit(Node n)
            {
                if(Bound(n)>=best)return;if(n.Left!=null){var a=n.Left;var b=n.Right!;if(Bound(a)>Bound(b))(a,b)=(b,a);Visit(a);Visit(b);return;}
                for(int i=n.Start;i<n.Start+n.Count;i++){var e=edges[i];var ab=e.B-e.A;double den=ab.Dot(ab);var delta=e.A+ab*(den>0?Math.Clamp((p-e.A).Dot(ab)/den,0,1):0)-p;best=Math.Min(best,delta.Dot(delta));}
            }
            Visit(root);return Math.Sqrt(best);
        }
    }
}
