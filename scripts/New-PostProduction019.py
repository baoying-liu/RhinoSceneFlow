import Rhino,System,json,os
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;assert doc.Objects.Count==0 and not doc.Modified and doc.Path is None
folder=os.path.join(OUTPUT_DIR,'postproduction019')
json.dump(dict(pid=EXPECTED_PID,previousSerial=int(doc.RuntimeSerialNumber)),open(os.path.join(folder,'new-before.json'),'w'))
assert Rhino.RhinoApp.RunScript('_-New _None',False)
print('Native New on owned empty B fixture requested')
