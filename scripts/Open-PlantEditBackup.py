import Rhino,System,json,os
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;assert doc.Objects.Count==0 and not doc.Modified,'Only a fresh B instance may load the recovery copy'
folder=os.path.join(OUTPUT_DIR,'plant-edit0171');record=json.load(open(os.path.join(folder,'backup.json')))
assert Rhino.RhinoApp.RunScript('_-Open "'+record['backup']+'" _Enter',False)
print('Opened backed-up user test state; original model preserved')
