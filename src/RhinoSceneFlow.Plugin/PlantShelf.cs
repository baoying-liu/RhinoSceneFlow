using Eto.Drawing;
using Eto.Forms;
namespace RhinoSceneFlow.Plugin;

internal sealed record PlantShelfItem(Guid Id,string Latin,string Name,string Path);

/// <summary>Viewport-only thumbnail drawing, with bounded owned bitmap cache.</summary>
internal sealed class PlantShelf:Scrollable
{
    private readonly ShelfCanvas canvas;
    private readonly int maximumHeight;
    private PlantShelfItem[] items=[];
    private Guid? selected;
    private bool tiles=true,dead;
    internal event Action<Guid>? SelectionChanged;
    internal event Action<Guid>? Activated;
    internal event Action<Guid>? AssetDropped;
    internal int Count=>items.Length;
    internal string View {get=>tiles?"tiles":"list";set{tiles=value!="list";canvas.Layout();canvas.Invalidate();}}
    internal string? SelectedKey
    {
        get=>selected?.ToString();
        set{selected=Guid.TryParse(value,out var id)&&items.Any(i=>i.Id==id)?id:null;canvas.Invalidate();}
    }
    internal PlantShelf(int height,bool acceptDrop=false)
    {
        maximumHeight=height;Height=height;ExpandContentWidth=true;ExpandContentHeight=false;AllowDrop=acceptDrop;canvas=new(this){AllowDrop=acceptDrop};Content=canvas;
        if(acceptDrop){DragEnter+=Enter;DragDrop+=Drop;canvas.DragEnter+=Enter;canvas.DragDrop+=Drop;}
    }
    private void Enter(object? sender,DragEventArgs e){if(e.Data.Text?.StartsWith("SceneFlowPlant:",StringComparison.Ordinal)==true)e.Effects=DragEffects.Copy;}
    private void Drop(object? sender,DragEventArgs e){if(!dead&&e.Data.Text is string text&&text.StartsWith("SceneFlowPlant:",StringComparison.Ordinal)&&Guid.TryParse(text[15..],out var id))AssetDropped?.Invoke(id);}
    internal void SetItems(IEnumerable<PlantShelfItem> source)
    {
        items=source.ToArray();if(selected.HasValue&&!items.Any(i=>i.Id==selected))selected=null;canvas.Layout();canvas.Invalidate();
    }
    internal object State()=>new{view=View,count=items.Length,selected,items=items.Select(i=>new{i.Id,i.Latin,i.Name}).ToArray(),cachedThumbnails=canvas.CacheCount};
    protected override void Dispose(bool disposing)
    {
        if(disposing&&!dead){dead=true;Content=null;canvas.Dispose();SelectionChanged=null;Activated=null;AssetDropped=null;}base.Dispose(disposing);
    }
    private sealed class ShelfCanvas:Drawable
    {
        private readonly PlantShelf owner;
        private readonly Dictionary<string,Bitmap?> cache=[];
        private readonly Font latin=new("Segoe UI",9,FontStyle.Italic),title=new(SystemFont.Default,9);
        private PointF? pressed;
        private int lastWidth=-1;
        internal int CacheCount=>cache.Count;
        private int Columns=>owner.tiles?Math.Max(1,(Math.Max(1,Width)+55)/110):1;
        private float CellWidth=>Math.Max(1,Width)/(float)Columns;
        private int CellHeight=>owner.tiles?(int)CellWidth+36:66;
        internal ShelfCanvas(PlantShelf owner){this.owner=owner;CanFocus=true;SizeChanged+=(_,_)=>{if(lastWidth!=Width){lastWidth=Width;Layout();}};}
        internal void Layout()
        {
            if(owner.dead)return;int natural=Math.Max(68,(int)Math.Ceiling(owner.items.Length/(double)Columns)*CellHeight);Height=natural;owner.Height=Math.Min(owner.maximumHeight,natural+4);
        }
        private int Hit(PointF point){int col=Math.Clamp((int)(point.X/CellWidth),0,Columns-1),row=Math.Max(0,(int)point.Y/CellHeight),index=row*Columns+col;return index<owner.items.Length?index:-1;}
        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);if(owner.dead||!e.Buttons.HasFlag(MouseButtons.Primary))return;int i=Hit(e.Location);if(i<0)return;
            Focus();pressed=e.Location;owner.selected=owner.items[i].Id;Invalidate();owner.SelectionChanged?.Invoke(owner.selected.Value);
        }
        protected override void OnMouseDoubleClick(MouseEventArgs e){base.OnMouseDoubleClick(e);int i=Hit(e.Location);if(!owner.dead&&i>=0)owner.Activated?.Invoke(owner.items[i].Id);}
        protected override void OnMouseUp(MouseEventArgs e){pressed=null;base.OnMouseUp(e);}
        protected override void OnKeyDown(KeyEventArgs e)
        {
            base.OnKeyDown(e);if(owner.dead||owner.items.Length==0)return;int index=Array.FindIndex(owner.items,i=>i.Id==owner.selected);
            int step=e.Key==Keys.Left?-1:e.Key==Keys.Right?1:e.Key==Keys.Up?-Columns:e.Key==Keys.Down?Columns:0;
            if(step!=0){index=Math.Clamp(index<0?0:index+step,0,owner.items.Length-1);owner.selected=owner.items[index].Id;owner.ScrollPosition=new(0,index/Columns*CellHeight);Invalidate();owner.SelectionChanged?.Invoke(owner.selected.Value);e.Handled=true;}
            else if(e.Key==Keys.Enter&&index>=0){owner.Activated?.Invoke(owner.items[index].Id);e.Handled=true;}
        }
        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);if(owner.dead)return;int i=Hit(e.Location);ToolTip=i<0?null:owner.items[i].Latin+"\n"+owner.items[i].Name;
            if(pressed.HasValue&&owner.selected.HasValue&&e.Buttons.HasFlag(MouseButtons.Primary)&&Math.Abs(e.Location.X-pressed.Value.X)+Math.Abs(e.Location.Y-pressed.Value.Y)>5)
            {pressed=null;DoDragDrop(new DataObject{Text="SceneFlowPlant:"+owner.selected},DragEffects.Copy);}
        }
        private Bitmap? Thumbnail(string path)
        {
            if(cache.TryGetValue(path,out var found))return found;
            if(cache.Count>=64){foreach(var old in cache.Values)old?.Dispose();cache.Clear();}
            try
            {
                using var source=new System.Drawing.Bitmap(path);double s=Math.Min(1,160.0/Math.Max(source.Width,source.Height));
                using var image=new System.Drawing.Bitmap(Math.Max(1,(int)(source.Width*s)),Math.Max(1,(int)(source.Height*s)),System.Drawing.Imaging.PixelFormat.Format32bppArgb);
                using(var g=System.Drawing.Graphics.FromImage(image)){g.InterpolationMode=System.Drawing.Drawing2D.InterpolationMode.HighQualityBicubic;g.DrawImage(source,0,0,image.Width,image.Height);}found=Ui.Bitmap(image);
            }
            catch(Exception ex) when(ex is IOException or ArgumentException or System.Runtime.InteropServices.ExternalException){found=null;}
            cache[path]=found;return found;
        }
        private void Text(Graphics g,Font font,Color color,float x,float y,float width,string value)
        {
            string text=value;while(text.Length>1&&g.MeasureString(font,text).Width>width)text=text[..^2]+"…";
            g.DrawText(font,color,x,y,text);
        }
        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);if(owner.dead)return;var g=e.Graphics;float width=CellWidth;int height=CellHeight;
            int first=Math.Max(0,owner.ScrollPosition.Y/height-1)*Columns,last=Math.Min(owner.items.Length,((owner.ScrollPosition.Y+Math.Max(70,owner.Height))/height+2)*Columns);
            if(owner.items.Length==0){g.DrawText(title,SystemColors.ControlText,8,12,"—");return;}
            for(int i=first;i<last;i++)
            {
                var item=owner.items[i];float x=i%Columns*width,y=i/Columns*height;bool active=item.Id==owner.selected;var rect=new RectangleF(x+3,y+3,width-6,height-6);
                g.FillRectangle(active?SystemColors.Highlight:SystemColors.ControlBackground,rect);g.DrawRectangle(active?SystemColors.Highlight:Colors.Gray,rect);
                float size=owner.tiles?width-14:52;var picture=new RectangleF(x+7,y+7,size,size);g.FillRectangle(Color.FromArgb(225,228,225),picture);
                var image=Thumbnail(item.Path);if(image!=null){float scale=Math.Min(picture.Width/image.Width,picture.Height/image.Height);float w=image.Width*scale,h=image.Height*scale;g.DrawImage(image,new RectangleF(picture.X+(picture.Width-w)/2,picture.Y+(picture.Height-h)/2,w,h));}
                else g.DrawText(title,Colors.Gray,picture.X+5,picture.Y+15,"PNG");
                var color=active?SystemColors.HighlightText:SystemColors.ControlText;float tx=owner.tiles?x+7:x+67,ty=owner.tiles?picture.Bottom+5:y+13,tw=owner.tiles?width-14:width-76;
                Text(g,latin,color,tx,ty,tw,item.Latin);Text(g,title,color,tx,ty+18,tw,item.Name==item.Latin?"":item.Name);
            }
        }
        protected override void Dispose(bool disposing){if(disposing){foreach(var b in cache.Values)b?.Dispose();cache.Clear();latin.Dispose();title.Dispose();}base.Dispose(disposing);}
    }
}
