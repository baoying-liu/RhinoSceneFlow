"""Refresh actual Named View additions, removals and rename, preserving settings by ID."""
import clr,Rhino,System,json,os
from Rhino.DocObjects import ViewInfo
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import ExportPanelController,McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;p=ExportPanelController.Find(doc.RuntimeSerialNumber);assert p is not None
assert all(o.Attributes.GetUserString('SceneFlowShadowResearch')=='20261022' for o in doc.Objects)
def state():return json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='panel_status',document=int(doc.RuntimeSerialNumber)))))['result']
before=state();target=next(v for v in before['views'] if '透视' in v['name'])
modified=doc.Modified;temporary='SceneFlow_Test_刷新临时';renamed=target['name']+'_刷新';added=False
try:
    assert doc.NamedViews.Rename(target['name'],renamed)
    p.RefreshNamedViews();s=state();row=next(v for v in s['views'] if v['id']==target['id'])
    assert row['name']==renamed and (row['width'],row['height'])==(target['width'],target['height'])
    info=ViewInfo(doc.Views.ActiveView.ActiveViewport);info.Name=temporary
    assert doc.NamedViews.Add(info)>=0;info.Dispose();added=True
    p.RefreshNamedViews();assert len(state()['views'])==len(before['views'])+1
    assert doc.NamedViews.Delete(temporary);added=False
    p.RefreshNamedViews();assert len(state()['views'])==len(before['views'])
    with open(os.path.join(OUTPUT_DIR,'panel','refresh-report.json'),'w') as f:json.dump(dict(ok=True,rename=True,added=True,removed=True,dimensionsPreserved=True),f,indent=2)
    print('Named View rename/add/remove refresh passed')
finally:
    if added:doc.NamedViews.Delete(temporary)
    if doc.NamedViews.FindByName(renamed)>=0:doc.NamedViews.Rename(renamed,target['name'])
    doc.Modified=modified;p.RefreshNamedViews()
