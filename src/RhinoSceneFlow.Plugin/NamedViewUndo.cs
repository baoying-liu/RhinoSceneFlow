using Rhino;
using Rhino.Commands;
using Rhino.FileIO;

namespace RhinoSceneFlow.Plugin;

/// <summary>NamedViewTable changes do not enter native object undo automatically.
/// Store owned metadata bytes; never retain a borrowed ViewInfo across delete/reopen.</summary>
internal static class NamedViewUndo
{
    private sealed record Rename(Entry Entry,string Target,string Reverse);
    private sealed class Entry(Guid id){internal Guid Id=id;internal byte[] Snapshot=[];internal ViewExportRow? Settings;}
    private sealed record Presence(Entry Entry,bool Present);
    private static readonly Dictionary<(uint,Guid),WeakReference<Entry>> entries=[];
    static NamedViewUndo(){RhinoDoc.CloseDocument+=Closed;}
    private static void Closed(object? sender,DocumentEventArgs e){foreach(var key in entries.Keys.Where(k=>k.Item1==e.Document.RuntimeSerialNumber).ToArray())entries.Remove(key);}
    internal static void Stop(){RhinoDoc.CloseDocument-=Closed;entries.Clear();}
    private static Entry Identity(RhinoDoc doc,Guid id)
    {
        var key=(doc.RuntimeSerialNumber,id);if(entries.TryGetValue(key,out var weak)&&weak.TryGetTarget(out var found))return found;
        if(entries.Count>256)foreach(var old in entries.Where(p=>!p.Value.TryGetTarget(out _)).Select(p=>p.Key).ToArray())entries.Remove(old);
        var entry=new Entry(id);entries[key]=new(entry);return entry;
    }
    internal static void Renamed(RhinoDoc doc,Guid id,string oldName,string newName)=>doc.AddCustomUndoEvent("重命名已命名视图",Restore,new Rename(Identity(doc,id),oldName,newName));
    internal static void Created(RhinoDoc doc,Guid id)=>doc.AddCustomUndoEvent("创建已命名视图",Restore,new Presence(Identity(doc,id),false));
    private static void Restore(object? sender,CustomUndoEventArgs e)
    {
        object? change=e.Tag;
        object? reverse=change switch{Rename r=>new Rename(r.Entry,r.Reverse,r.Target),Presence p=>new Presence(p.Entry,!p.Present),_=>null};if(reverse==null)return;
        e.Document.AddCustomUndoEvent(e.ActionDescription,Restore,reverse);uint serial=e.Document.RuntimeSerialNumber;
        // Native replay must finish before touching its tables.
        Eto.Forms.Application.Instance.AsyncInvoke(()=>
        {
            var doc=RhinoDoc.FromRuntimeSerialNumber(serial);if(doc?.IsAvailable!=true||doc.IsClosing)return;
            bool recording=doc.UndoRecordingEnabled;
            try
            {
                doc.UndoRecordingEnabled=false;
                if(change is Rename r)
                {
                    if(NamedViewExportService.List(doc).Any(v=>v.Id!=r.Entry.Id&&v.Name.Equals(r.Target,StringComparison.OrdinalIgnoreCase)))throw new InvalidOperationException("无法恢复视图名称；名称被其他视图占用。");
                    for(int i=0;i<doc.NamedViews.Count;i++){using var view=doc.NamedViews[i];if(view.NamedViewId!=r.Entry.Id)continue;if(!doc.NamedViews.Rename(i,r.Target))throw new InvalidOperationException("无法恢复视图名称。");break;}
                }
                else if(change is Presence p)
                {
                    if(!p.Present)
                    {
                        p.Entry.Settings=WorkbenchService.Settings(doc).FirstOrDefault(r=>r.Id==p.Entry.Id)?.Copy();
                        for(int i=0;i<doc.NamedViews.Count;i++)
                        {
                            using var view=doc.NamedViews[i];if(view.NamedViewId!=p.Entry.Id)continue;
                            using var file=new File3dm();file.NamedViews.Add(view);p.Entry.Snapshot=file.ToByteArray();
                            if(!doc.NamedViews.Delete(i))throw new InvalidOperationException("无法撤销创建的视图。");break;
                        }
                    }
                    else if(p.Entry.Snapshot.Length>0)
                    {
                        using var file=File3dm.FromByteArray(p.Entry.Snapshot);using var view=file.NamedViews[0];
                        if(NamedViewExportService.List(doc).Any(v=>v.Name.Equals(view.Name,StringComparison.OrdinalIgnoreCase)))throw new InvalidOperationException("无法重做创建视图：名称已被其他视图占用。");
                        int index=doc.NamedViews.Add(view);if(index<0)throw new InvalidOperationException("无法恢复已命名视图。");using var restored=doc.NamedViews[index];entries.Remove((serial,p.Entry.Id));p.Entry.Id=restored.NamedViewId;entries[(serial,p.Entry.Id)]=new(p.Entry);
                    }
                    ExportPanelController.Find(serial)?.RefreshNamedViews();
                    if(p.Present&&p.Entry.Settings is {} settings){settings=settings.Copy();settings.Id=p.Entry.Id;WorkbenchService.Configure(doc,settings);}
                }
                doc.Modified=true;
            }
            catch(Exception ex){RhinoApp.WriteLine("SceneFlow 视图撤销："+ex.Message);}
            finally{doc.UndoRecordingEnabled=recording;}
        });
    }
}
