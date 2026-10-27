import Rhino,System,json,os
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
print(json.dumps(dict(ok=True,pid=EXPECTED_PID,objects=__rhino_doc__.Objects.Count,namedViews=__rhino_doc__.NamedViews.Count,aliveAfterUiIdle=True)))
