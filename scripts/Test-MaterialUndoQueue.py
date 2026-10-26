import Rhino,System,json,clr
from Eto.Forms import UITimer
D=__rhino_doc__;app=System.AppDomain.CurrentDomain
timer=UITimer();timer.Interval=.1
def undo(sender,args):
 timer.Stop();app.SetData('SceneFlowUndoResult',D.Undo())
timer.Elapsed+=undo;timer.Start();app.SetData('SceneFlowUndoTimer',timer)
print('queued')
