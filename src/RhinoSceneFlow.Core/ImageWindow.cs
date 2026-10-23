namespace RhinoSceneFlow.Core;

public sealed class ImageWindow(IPsdImage source,int left,int top,int width,int height) : IPsdImage
{
    public int Width=>width;
    public int Height=>height;
    public IReadOnlyList<ColorGroup> Groups=>source.Groups;
    public IReadOnlyList<LayerBounds> GetVisibleLayers(CancellationToken cancellation=default)=>source.GetVisibleLayers(cancellation)
        .Select(b=>new LayerBounds(b.Group,Math.Max(0,b.Left-left),Math.Max(0,b.Top-top),Math.Min(width,b.Right-left),Math.Min(height,b.Bottom-top)))
        .Where(b=>b.Right>b.Left&&b.Bottom>b.Top).ToArray();
    public byte LayerAlpha(int group,int x,int y)=>source.LayerAlpha(group,left+x,top+y);
    public byte LayerChannel(int group,int channel,int x,int y)=>source.LayerChannel(group,channel,left+x,top+y);
    public byte CompositeChannel(int channel,int x,int y)=>source.CompositeChannel(channel,left+x,top+y);
    public void ReadLayerRow(int group,int channel,int y,int offset,Span<byte> row)=>source.ReadLayerRow(group,channel,top+y,left+offset,row);
}
