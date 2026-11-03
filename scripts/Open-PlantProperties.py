import Rhino,System,json,os
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
record=json.load(open(os.path.join(OUTPUT_DIR,'properties017','setup.json')))
doc=__rhino_doc__
assert (doc.Objects.Count==0 and not doc.Modified) or (doc.Path==record['model'] and not doc.Modified),'Do not overwrite unrelated/unsaved work'
assert Rhino.RhinoApp.RunScript('_-Open "'+record['model']+'" _Enter',False)
print('Native Open requested for owned Properties fixture')
