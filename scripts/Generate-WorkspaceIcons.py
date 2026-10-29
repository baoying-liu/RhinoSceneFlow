"""Deterministic source icons; Pillow is a development-only dependency."""
from PIL import Image,ImageDraw
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'src/RhinoSceneFlow.Plugin/Resources';root.mkdir(exist_ok=True)
for name,color in [('Materials','#54b3ad'),('Library','#a28bcb'),('Uv','#73a7df'),('Planting','#81b775'),('Export','#d6a866')]:
 im=Image.new('RGBA',(64,64));d=ImageDraw.Draw(im);d.rounded_rectangle((3,3,61,61),radius=13,fill=color)
 if name=='Materials':
  d.ellipse((14,14,50,50),fill='#f1f4f5');d.pieslice((14,14,50,50),90,270,fill='#24474b');d.ellipse((19,19,29,29),fill='#ffffff')
 elif name=='Library':
  for y in [15,29,43]:
   d.ellipse((13,y,23,y+10),fill='white');d.rounded_rectangle((29,y+2,51,y+8),radius=2,fill='white')
 elif name=='Uv':
  d.rectangle((14,14,50,50),outline='white',width=3)
  for n in [26,38]:d.line((n,14,n,50),fill='white',width=2);d.line((14,n,50,n),fill='white',width=2)
 elif name=='Planting':
  d.ellipse((13,13,38,38),fill='white');d.ellipse((28,20,50,42),fill='#e0eddc');d.line((31,29,31,52),fill='white',width=4)
 else:
  for y in [39,28,17]:d.polygon([(13,y+5),(32,y-3),(51,y+5),(32,y+13)],fill='#fff7e9',outline='#9a7539',width=2)
 im.save(root/(name+'.ico'),sizes=[(16,16),(24,24),(32,32),(48,48),(64,64)])
