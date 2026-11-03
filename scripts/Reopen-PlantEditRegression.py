import Rhino,System,json,os
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
record=json.load(open(os.path.join(OUTPUT_DIR,'plant-edit0171','saved.json')))
assert __rhino_doc__.Path==record['path'] and not __rhino_doc__.Modified
assert Rhino.RhinoApp.RunScript('_-Open "'+record['path']+'" _Enter',False)
