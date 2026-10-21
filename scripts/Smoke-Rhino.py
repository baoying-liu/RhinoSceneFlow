"""Run with Rhino MCP run_python in a fresh B-channel test document. Keeps the demo scene."""
import json
import os
import System
import Rhino
import clr
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
clr.AddReference('RhinoSceneFlow.Core')
from RhinoSceneFlow.Core import CameraProjection, Vec3
from System.Drawing import Color
from Rhino.Geometry import Point3d, Mesh, BoundingBox
from Rhino.DocObjects import Layer, ObjectAttributes
from Rhino.Display import DefinedViewportProjection, DisplayModeDescription, ViewCapture

assert System.Diagnostics.Process.GetCurrentProcess().Id == EXPECTED_PID
doc = __rhino_doc__
assert Rhino.RhinoDoc.ActiveDoc.RuntimeSerialNumber == doc.RuntimeSerialNumber
assert doc.Objects.Count == 0, 'Smoke test requires an empty sandbox document'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def layer(name, color, parent=None):
    item = Layer()
    item.Name = name
    item.Color = color
    if parent is not None:
        item.ParentLayerId = doc.Layers[parent].Id
    return doc.Layers.Add(item)

red = layer('SceneFlow_Building', Color.FromArgb(230, 80, 50))
red2 = layer('SceneFlow_SameRed', Color.FromArgb(230, 80, 50))
blue = layer('SceneFlow_Paving', Color.FromArgb(50, 130, 200))
yellow = layer('SceneFlow_Locked', Color.FromArgb(240, 200, 40))
green = layer('SceneFlow_HiddenObject', Color.Green)
parent = layer('SceneFlow_HiddenParent', Color.Purple)
child = layer('SceneFlow_HiddenChild', Color.Purple, parent)

def panel(layer_index, x0, y0, x1, y1, z):
    mesh = Mesh()
    for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        mesh.Vertices.Add(x, y, z)
    mesh.Faces.AddFace(0, 1, 2, 3)
    mesh.Normals.ComputeNormals()
    attributes = ObjectAttributes()
    attributes.LayerIndex = layer_index
    return doc.Objects.AddMesh(mesh, attributes)

panel(blue, 0, 0, 10, 8, 0)
front_id = panel(red, 3, 2, 7, 6, 2)
panel(red2, 11, 0, 13, 2, 0)
locked_id = panel(yellow, 0, 9, 2, 11, 0)
doc.Objects.Lock(locked_id, True)
hidden_id = panel(green, 0, 0, 10, 8, 3)
doc.Objects.Hide(hidden_id, True)
panel(child, 0, 0, 10, 8, 4)
doc.Layers[parent].IsVisible = False
doc.Layers[parent].CommitChanges()
doc.Objects.Select(front_id)

view = doc.Views.ActiveView
vp = view.ActiveViewport
vp.DisplayMode = DisplayModeDescription.FindByName('Shaded')
bounds = BoundingBox(Point3d(-1, -1, -1), Point3d(14, 12, 3))
report = {'pid': EXPECTED_PID, 'document_serial': doc.RuntimeSerialNumber, 'cases': [], 'api_checks': []}
def api(operation, **kwargs):
    request = dict(apiVersion=1, operation=operation, document=int(doc.RuntimeSerialNumber), **kwargs)
    return json.loads(McpApi.Execute(json.dumps(request)))
report['describe'] = api('describe')
assert report['describe']['ok']
assert report['describe']['result']['version'] == '0.2.0'
export_dir = os.path.join(os.path.dirname(OUTPUT_DIR), 'exports')
assert api('configure_export', directory=export_dir)['ok']
assert api('status')['result']['defaultDirectory'] == export_dir
for invalid_request, expected_code in [
    ({'apiVersion':2, 'operation':'describe'}, 'unsupported_version'),
    ({'apiVersion':1, 'operation':'status', 'document':4294967295}, 'document_not_found'),
    ({'apiVersion':1, 'operation':'missing'}, 'unsupported_operation')]:
    response = json.loads(McpApi.Execute(json.dumps(invalid_request)))
    assert not response['ok'] and response['error']['code'] == expected_code, response
    report['api_checks'].append(expected_code)

def state():
    return {'modified': doc.Modified, 'objects': doc.Objects.Count,
        'selection': sorted(str(o.Id) for o in doc.Objects.GetSelectedObjects(False, False)),
        'camera': [vp.CameraLocation.X, vp.CameraLocation.Y, vp.CameraLocation.Z,
            vp.CameraDirection.X, vp.CameraDirection.Y, vp.CameraDirection.Z],
        'mode': str(vp.DisplayMode.Id),
        'layers': [(str(l.Id), l.Color.ToArgb(), l.IsVisible, l.IsLocked) for l in doc.Layers if not l.IsDeleted]}

for name, projection in [('top', DefinedViewportProjection.Top), ('perspective', DefinedViewportProjection.Perspective)]:
    vp.SetProjection(projection, 'SceneFlow_' + name, True)
    vp.ZoomBoundingBox(bounds)
    doc.Views.Redraw()
    before = state()
    export = api('export_psd', width=512, viewportId=str(vp.Id))
    assert export['ok'], str(export)
    path = export['result']['path']
    assert os.path.isfile(path), 'Export file missing: ' + name
    assert api('export_psd', width=512, path=path)['ok'] is False, 'Existing output must be protected'
    assert api('export_psd', width=1)['ok'] is False, 'Invalid size must be rejected'
    assert api('export_psd', width=512, viewportId='00000000-0000-0000-0000-000000000000')['ok'] is False
    assert state() == before, 'Export changed document state: ' + name
    capture = ViewCapture()
    capture.Width = 512
    capture.Height = max(1, int(round(512.0 * vp.Size.Height / vp.Size.Width)))
    capture.DrawGrid = False
    capture.DrawAxes = False
    capture.DrawGridAxes = False
    bitmap = capture.CaptureToBitmap(view)
    if bitmap:
        bitmap.Save(os.path.join(OUTPUT_DIR, name + '-viewport.png'))
        bitmap.Dispose()
    probes = []
    frustum = vp.GetFrustum()
    assert frustum[0]
    def vector(value):
        return Vec3(value.X, value.Y, value.Z)
    camera = CameraProjection(vector(vp.CameraLocation), vector(vp.CameraX), vector(vp.CameraY), vector(vp.CameraZ),
        *frustum[1:], vp.IsParallelProjection)
    projection_error = 0.0
    for label, point, color in [('front', Point3d(5,4,2), [230,80,50]), ('paving', Point3d(1,1,0), [50,130,200]),
                                ('same_red', Point3d(12,1,0), [230,80,50]), ('locked', Point3d(1,10,0), [240,200,40])]:
        screen = vp.WorldToClient(point)
        clip = camera.Project(vector(point))
        expected_x = (clip.X / clip.W + 1) * vp.Size.Width / 2
        expected_y = (1 - clip.Y / clip.W) * vp.Size.Height / 2
        projection_error = max(projection_error, abs(expected_x-screen.X), abs(expected_y-screen.Y))
        probes.append({'label': label, 'x': screen.X * 512 / vp.Size.Width,
            'y': screen.Y * capture.Height / vp.Size.Height, 'rgb': color})
    report['cases'].append({'name': name, 'path': path, 'width':512, 'height':capture.Height,
        'state_unchanged': True, 'probes':probes, 'export':export['result'], 'projectionMaxError':projection_error})
    assert projection_error < 0.01, ('Projection differs from Rhino', name, projection_error)

options = Rhino.FileIO.FileWriteOptions()
options.SuppressDialogBoxes = True
doc.WriteFile(os.path.join(OUTPUT_DIR, 'SceneFlow-B-smoke.3dm'), options)
report['complete'] = True
with open(os.path.join(OUTPUT_DIR, 'smoke.json'), 'w') as handle:
    json.dump(report, handle, indent=2)
print(json.dumps({'complete':True, 'pid':EXPECTED_PID, 'report':os.path.join(OUTPUT_DIR, 'smoke.json'),
    'exports':[case['path'] for case in report['cases']]}))
