import Rhino,System,json,os
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
receipt=json.load(open(os.path.join(OUTPUT_DIR,'plants015','delivery.json')))
assert __rhino_doc__.Objects.Count==0 and not __rhino_doc__.Modified
assert Rhino.RhinoApp.RunScript('_-Open "'+receipt['model']+'" _Enter',False)
