using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;

namespace RhinoSceneFlow.Plugin;

// Derived mesh replacements deliberately do not enter Rhino's undo stack. Keep parameter
// snapshots in a native custom record so undo does not depend on an obsolete mesh instance.
internal static class PlantParameterUndo
{
    private sealed record Snapshot(uint Document,Guid Object,string Json,string Name);
    private sealed record Change(Snapshot Target,Snapshot Reverse);
    private static readonly Dictionary<(uint,Guid),Snapshot> pending=[];
    internal static void Start(){Command.UndoRedo+=Ended;RhinoDoc.CloseDocument+=Closed;}
    internal static void Stop(){Command.UndoRedo-=Ended;RhinoDoc.CloseDocument-=Closed;pending.Clear();}
    internal static void Record(RhinoDoc doc,RhinoObject before,string json,string name)
    {
        var old=new Snapshot(doc.RuntimeSerialNumber,before.Id,before.Attributes.GetUserString(PlantGroups.Key)!,before.Name);
        var next=new Snapshot(doc.RuntimeSerialNumber,before.Id,json,name);
        if(old.Json!=next.Json||old.Name!=next.Name)doc.AddCustomUndoEvent("植物组合参数",Restore,new Change(old,next));
    }
    private static void Restore(object? sender,CustomUndoEventArgs e)
    {
        if(e.Tag is not Change change)return;
        // Do not modify the document while Rhino is replaying its native object records.
        pending[(change.Target.Document,change.Target.Object)]=change.Target;
        e.Document.AddCustomUndoEvent("植物组合参数",Restore,new Change(change.Reverse,change.Target));
    }
    private static void Ended(object? sender,UndoRedoEventArgs e)
    {
        if(!e.IsEndUndo&&!e.IsEndRedo)return;
        foreach(var (key,snapshot) in pending.ToArray())
        {
            pending.Remove(key);var doc=RhinoDoc.FromRuntimeSerialNumber(snapshot.Document);
            if(doc?.IsAvailable!=true||doc.IsClosing||doc.Objects.FindId(snapshot.Object) is not {} obj)continue;
            bool undo=doc.UndoRecordingEnabled;
            try
            {
                doc.UndoRecordingEnabled=false;var a=obj.Attributes.Duplicate();a.SetUserString(PlantGroups.Key,snapshot.Json);a.Name=snapshot.Name;
                if(!doc.Objects.ModifyAttributes(snapshot.Object,a,true))RhinoApp.WriteLine("SceneFlow: 无法恢复植物组合参数。");
            }
            finally{doc.UndoRecordingEnabled=undo;}
        }
    }
    private static void Closed(object? sender,DocumentEventArgs e){foreach(var key in pending.Keys.Where(k=>k.Item1==e.Document.RuntimeSerialNumber).ToArray())pending.Remove(key);}
}
