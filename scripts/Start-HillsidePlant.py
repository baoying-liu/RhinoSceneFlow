"""Start the real SceneFlow plant workflow; preserve existing requests and source verification."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__
folder=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Hillside-Retreat'));os.makedirs(folder,exist_ok=True)
path=os.path.join(folder,'tree-job.json');assert not os.path.exists(path),'Existing request must be resumed'
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
job=api('material_chat_start',conversation='请为山地小屋景观演示生成一株真实植物河桦 Betula nigra 的完整单株透明背景 PNG 素材。先核实该物种学名和科名以及真实来源页面；若库中已有同物种且符合要求的素材可优先返回，否则实际生成。要求夏季绿色叶片，自然疏透的树冠，完整树梢、树冠和树干基部，年轻多干或少量分枝的河桦，参考表现高度8米（估计表现尺寸，不是实测），正面平视，光线中性柔和，不要盆、地面、人物、投影或背景。用于Rhino中自动朝向相机的2D树木。',reuseSimilar=True,heightMeters=8)
with open(path,'w') as f:json.dump(job,f,indent=2)
print(json.dumps(dict(job=job['id'],status=job['status'],stage=job['stage'])))
