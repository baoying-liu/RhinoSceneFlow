namespace RhinoSceneFlow.Core;

/// <summary>Row-streamed staging for large exports; RAM stays bounded by a render tile.
/// Flat layers store alpha only; captured display modes store real RGBA.</summary>
public sealed class DiskPassImage : IPsdImage,IDisposable
{
    private readonly string directory;
    private readonly FileStream composite;
    private readonly FileStream[] alpha;
    private readonly bool pixelRgb;
    private readonly LayerBounds[] bounds;
    private readonly byte[] rgbaRow;
    private int cachedY=-1;
    public int Width{get;}
    public int Height{get;}
    public IReadOnlyList<ColorGroup> Groups{get;}
    public DiskPassImage(string staging,int width,int height,IReadOnlyList<ColorGroup> groups,bool pixelRgb=false)
    {
        if(width<1||height<1||width>8192||height>8192||groups.Count==0)throw new ArgumentException("Invalid staged image.");
        Width=width;Height=height;Groups=groups;this.pixelRgb=pixelRgb;
        directory=Path.Combine(staging,Guid.NewGuid().ToString("N"));Directory.CreateDirectory(directory);
        composite=new(Path.Combine(directory,"rgba"),FileMode.Create,FileAccess.ReadWrite,FileShare.Read);composite.SetLength((long)width*height*4);
        alpha=groups.Select((_,i)=>new FileStream(Path.Combine(directory,"alpha"+i),FileMode.Create,FileAccess.ReadWrite,FileShare.Read)).ToArray();
        foreach(var f in alpha)f.SetLength((long)width*height);
        bounds=Enumerable.Range(0,groups.Count).Select(g=>new LayerBounds(g,width,height,0,0)).ToArray();rgbaRow=new byte[width*4];
    }
    public void WriteTile(int left,int top,IPsdImage tile,CancellationToken cancellation=default)
    {
        if(left<0||top<0||left+tile.Width>Width||top+tile.Height>Height||tile.Groups.Count!=Groups.Count)throw new ArgumentException("Invalid tile.");
        var row=new byte[tile.Width];var rgba=new byte[tile.Width*4];
        for(int y=0;y<tile.Height;y++)
        {
            cancellation.ThrowIfCancellationRequested();
            for(int c=0;c<4;c++)
            {tile.ReadCompositeRow(c,y,row);for(int x=0;x<tile.Width;x++)rgba[x*4+c]=row[x];}
            WriteRgbaRow(top+y,left,rgba);
            for(int g=0;g<Groups.Count;g++)
            {
                tile.ReadLayerRow(g,3,y,0,row);WriteAlpha(g,top+y,left,row);
            }
        }
    }
    public void WriteRgbaRow(int y,int left,ReadOnlySpan<byte> rgba)
    {
        composite.Position=((long)y*Width+left)*4;composite.Write(rgba);cachedY=-1;
        if(pixelRgb)
        {var a=new byte[rgba.Length/4];for(int x=0;x<a.Length;x++)a[x]=rgba[x*4+3];WriteAlpha(0,y,left,a);}
    }
    private void WriteAlpha(int group,int y,int left,ReadOnlySpan<byte> row)
    {
        var file=alpha[group];file.Position=(long)y*Width+left;file.Write(row);
        int first=-1,last=-1;for(int x=0;x<row.Length;x++)if(row[x]!=0){if(first<0)first=x;last=x;}
        if(first<0)return;var b=bounds[group];bounds[group]=new(group,Math.Min(b.Left,left+first),Math.Min(b.Top,y),Math.Max(b.Right,left+last+1),Math.Max(b.Bottom,y+1));
    }
    private void ReadRgba(int y)
    {if(cachedY==y)return;composite.Position=(long)y*Width*4;composite.ReadExactly(rgbaRow);cachedY=y;}
    public IReadOnlyList<LayerBounds> GetVisibleLayers(CancellationToken cancellation=default)=>bounds.Where(b=>b.Right>b.Left).ToArray();
    public void ReadCompositeRow(int channel,int y,Span<byte> row)
    {ReadRgba(y);for(int x=0;x<row.Length;x++)row[x]=rgbaRow[x*4+channel];}
    public void ReadLayerRow(int group,int channel,int y,int left,Span<byte> row)
    {
        if(channel==3){alpha[group].Position=(long)y*Width+left;alpha[group].ReadExactly(row);}
        else if(pixelRgb){ReadRgba(y);for(int x=0;x<row.Length;x++)row[x]=rgbaRow[(left+x)*4+channel];}
        else row.Fill(channel==0?Groups[group].Color.R:channel==1?Groups[group].Color.G:Groups[group].Color.B);
    }
    public byte LayerAlpha(int group,int x,int y){alpha[group].Position=(long)y*Width+x;return (byte)alpha[group].ReadByte();}
    public byte LayerChannel(int group,int channel,int x,int y){Span<byte> b=stackalloc byte[1];ReadLayerRow(group,channel,y,x,b);return b[0];}
    public byte CompositeChannel(int channel,int x,int y){ReadRgba(y);return rgbaRow[x*4+channel];}
    public void Dispose(){composite.Dispose();foreach(var f in alpha)f.Dispose();if(Directory.Exists(directory))Directory.Delete(directory,true);}
}
