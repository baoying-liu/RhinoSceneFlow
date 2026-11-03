import Rhino,System,json,os
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Hillside-Retreat'));model=json.load(open(os.path.join(folder,'views.json')))['model'];doc=__rhino_doc__
assert doc.Path==model and not doc.Modified,'Preserve unrelated or unsaved work'
with open(os.path.join(folder,'reopen-before.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),model=model),f)
assert Rhino.RhinoApp.RunScript('_-Open "'+model+'" _Enter',False)
print('Owned Hillside model reopened')
