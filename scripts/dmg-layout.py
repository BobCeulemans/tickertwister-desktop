#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Build-only requirements: pillow, ds-store, mac-alias (not bundled at runtime).
from pathlib import Path
import sys
from PIL import Image,ImageDraw,ImageFont
from ds_store import DSStore
from mac_alias import Alias
root=Path(sys.argv[1]);root.mkdir(parents=True,exist_ok=True);(root/'.background').mkdir(exist_ok=True)
# Retina background: 2 physical pixels per Finder point.
im=Image.new('RGB',(1360,1040),'#f5f3ec')
class RetinaDraw:
 def __init__(self,image): self.draw=ImageDraw.Draw(image)
 def __getattr__(self,name):
  def call(xy,*args,**kw):
   def scaled(v): return tuple(scaled(x) for x in v) if isinstance(v,(tuple,list)) else v*2
   for key in ('width','radius'):
    if key in kw: kw[key]*=2
   return getattr(self.draw,name)(scaled(xy),*args,**kw)
  return call
d=RetinaDraw(im)
font='/System/Library/Fonts/Supplemental/Arial.ttf'
f=lambda size:ImageFont.truetype(font,size*2)
d.rectangle((0,0,680,112),fill='#173e34')
d.text((100,24),'Ticker',font=f(34),fill='#ffffff')
d.text((100+f(34).getlength('Ticker')/2,24),'twister',font=f(34),fill='#e1bd78')
d.text((102,74),'DESKTOP  /  QUALITY. VALUE. PATIENCE.',font=f(12),fill='#e3eae1')
logo=Image.open(Path(__file__).resolve().parents[1]/'web/app-icon.png').convert('RGBA').resize((96,96),Image.Resampling.LANCZOS)
im.paste(logo,(64,48),logo)
for cx in [170,510]:d.rounded_rectangle((cx-94,155,cx+94,315),radius=24,fill='white',outline='#d8dfd2',width=2)
d.text((110,128),'1  Drag the app',font=f(16),fill='#173e34');d.text((438,128),'2  To Applications',font=f(16),fill='#173e34')
# Curved arrow, deliberately kept clear of the clickable icons.
points=[]
for i in range(81):
 t=i/80;x=(1-t)**2*278+2*(1-t)*t*340+t*t*402;y=(1-t)**2*242+2*(1-t)*t*180+t*t*242;points.append((x,y))
d.line(points,fill='#b58a44',width=7);d.polygon([(402,242),(380,234),(396,219)],fill='#b58a44')
d.text((130,348),'Drag the app into Applications to install.',font=f(17),fill='#173e34')
d.line((32,385,648,385),fill='#d8dfd2',width=2)
d.text((32,423),'License, source code and guides',font=f(14),fill='#5e7165')
d.text((32,446),'Copyright ©2026 Bob Ceulemans · All Rights Reserved.',font=f(10),fill='#5e7165')
im.save(root/'.background/installer.tiff',dpi=(144,144))
if '--background-only' in sys.argv: sys.exit(0)
with DSStore.open(str(root/'.DS_Store'),'w+') as ds:
 ds['.']['bwsp']={'ShowStatusBar':False,'ShowToolbar':False,'ShowTabView':False,'ShowPathbar':False,'ShowSidebar':False,'ContainerShowSidebar':False,'WindowBounds':'{{160, 140}, {680, 570}}'}
 ds['.']['icvp']={'viewOptionsVersion':1,'backgroundType':2,'backgroundImageAlias':Alias.for_file(str(root/'.background/installer.tiff')).to_bytes(),'iconSize':64.0,'textSize':12.0,'scrollPositionX':0.0,'scrollPositionY':0.0,'backgroundColorRed':1.0,'backgroundColorGreen':1.0,'backgroundColorBlue':1.0,'gridSpacing':100.0,'gridOffsetX':0.0,'gridOffsetY':0.0,'arrangeBy':'none','labelOnBottom':True,'showItemInfo':False,'showIconPreview':True}
 ds['.']['vSrn']=('long',1);ds['.']['icvl']=('type',b'icnv')
 ds['Tickertwister Desktop.app']['Iloc']=(170,228)
 ds['Applications']['Iloc']=(510,228)
 ds['Documentatie']['Iloc']=(575,445)
print('Finder layout written:',root)
