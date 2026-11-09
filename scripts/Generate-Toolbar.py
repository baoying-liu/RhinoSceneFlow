"""Generate SceneFlow's native RUI from existing project icons (Pillow dev dependency)."""
import base64, io, uuid, xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
NS=uuid.UUID('b9e785f9-89ac-4477-810d-f12c0ed4ce52')
def uid(key):return str(uuid.uuid5(NS,key))
def localized(parent,tag,en,zh):
    e=ET.SubElement(parent,tag)
    ET.SubElement(e,'locale_1033').text=en
    ET.SubElement(e,'locale_2052').text=zh

entries=[('Workspace','工作区','RhinoSceneFlow','Materials'),('AI assets','AI 素材','RhinoSceneFlowMaterials','Materials'),
 ('Materials','材质库','RhinoSceneFlowMaterialLibrary','Library'),('UV tools','UV 工具','RhinoSceneFlowUVTools','Uv'),
 ('Planting','植物库与种植','RhinoSceneFlowPlant','Planting'),('Plants List','植物组合列表','RhinoSceneFlowPlantsList','Planting'),
 ('Properties','属性','RhinoSceneFlowProperties','Uv'),('PSD export','PSD 导出','RhinoSceneFlowPanel','Export'),
 ('AI Studio','AI 后期','RhinoSceneFlowPostProduction','Export')]
r=ET.Element('RhinoUI',major_ver='2',minor_ver='0',guid=uid('file'),localize='True',default_language_id='1033')
ET.SubElement(r,'extend_rhino_menus');ET.SubElement(r,'menus')
groups=ET.SubElement(r,'tool_bar_groups');group=ET.SubElement(groups,'tool_bar_group',guid=uid('group'),single_file='True',hide_single_tab='True',point_floating='100,100')
localized(group,'text','SceneFlow','SceneFlow')
gi=ET.SubElement(group,'tool_bar_group_item',guid=uid('group-item'),major_version='1',minor_version='1')
localized(gi,'text','SceneFlow','SceneFlow');ET.SubElement(gi,'tool_bar_id').text=uid('toolbar')
bars=ET.SubElement(r,'tool_bars');bar=ET.SubElement(bars,'tool_bar',guid=uid('toolbar'));localized(bar,'text','SceneFlow','SceneFlow')
macros=ET.SubElement(r,'macros')
for en,zh,cmd,icon in entries:
    item=ET.SubElement(bar,'tool_bar_item',guid=uid('button-'+cmd));ET.SubElement(item,'left_macro_id').text=uid(cmd)
    m=ET.SubElement(macros,'macro_item',guid=uid(cmd),bitmap_id=uid('icon-'+cmd))
    for tag in ('text','tooltip','help_text'):localized(m,tag,en,zh)
    ET.SubElement(m,'script').text='! _'+cmd
bitmaps=ET.SubElement(r,'bitmaps')
for tag,size in [('small_bitmap',16),('normal_bitmap',24),('large_bitmap',32)]:
    sheet=Image.new('RGBA',(size*len(entries),size))
    e=ET.SubElement(bitmaps,tag,item_width=str(size),item_height=str(size))
    for i,(_,_,cmd,icon) in enumerate(entries):
        im=Image.open(ROOT/'src/RhinoSceneFlow.Plugin/Resources'/f'{icon}.ico').convert('RGBA').resize((size,size),Image.Resampling.LANCZOS)
        sheet.paste(im,(size*i,0));ET.SubElement(e,'bitmap_item',guid=uid('icon-'+cmd),index=str(i))
    data=io.BytesIO();sheet.save(data,format='PNG');ET.SubElement(e,'bitmap').text=base64.b64encode(data.getvalue()).decode()
ET.indent(r)
ET.ElementTree(r).write(ROOT/'src/RhinoSceneFlow.Plugin/RhinoSceneFlow.rui',encoding='utf-8',xml_declaration=True)
print('Generated SceneFlow RUI: 9 commands, bilingual labels, 16/24/32 px icons')
