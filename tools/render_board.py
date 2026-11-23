"""Render board geometry directly from the supplied KiCad file, without KiCad."""
import re, math, json
from paths import BUILD, PCB, DESIGN, GENERATED
from appearance import load_config,board_artwork_canvas
from PIL import Image,ImageDraw
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, FancyBboxPatch
from matplotlib.collections import LineCollection
s=PCB.read_text()
(BUILD/'board').mkdir(parents=True, exist_ok=True)
tokens=re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',s)
def parse(i):
 a=[]; i+=1
 while tokens[i]!=')':
  if tokens[i]=='(':
   v,i=parse(i); a.append(v)
  else:
   t=tokens[i]; a.append(json.loads(t) if t.startswith('"') else t); i+=1
 return a,i+1
board,_=parse(0)
def kids(a,k): return [x for x in a if isinstance(x,list) and x and x[0]==k]
def get(a,k,d=None):
 v=kids(a,k); return v[0][1:] if v else (d or [])
def xy(a,k): return np.array(list(map(float,get(a,k)[:2])))
def layer(a): return get(a,'layer',[''])[0]
def prop(a,k): return next((x[2] for x in kids(a,'property') if x[1]==k),'')
def arcpts(a):
 p,q,r=[xy(a,k) for k in ['start','mid','end']]
 try: c=np.linalg.solve(2*np.array([q-p,r-p]),np.array([q@q-p@p,r@r-p@p]))
 except np.linalg.LinAlgError: return np.array([p,q,r])
 t=[math.atan2(*(v-c)[::-1]) for v in [p,q,r]]
 end=(t[2]-t[0])%(2*np.pi); mid=(t[1]-t[0])%(2*np.pi)
 if mid>end: end-=2*np.pi
 ang=np.linspace(t[0],t[0]+end,35)
 return c+np.linalg.norm(p-c)*np.column_stack([np.cos(ang),np.sin(ang)])
footprints=kids(board,'footprint')
CFG=load_config()

def render(ax,side,template=False):
 ax.set_facecolor('none' if template else '#111a26'); ax.set_aspect('equal'); ax.axis('off')
 ax.set_xlim(121,206); ax.set_ylim(117,43)
 if side=='B': ax.invert_xaxis()
 boardpatch=FancyBboxPatch((128.25,50),70,60,boxstyle='round,pad=0,rounding_size=1',fc='none' if template else CFG['board']['colour'],ec='#43678b',lw=.5 if template else 1.2,zorder=1)
 ax.add_patch(boardpatch)
 if template:
  for x in np.arange(128.25,198.26,5):ax.plot([x,x],[50,110],color='#b8c2ce',alpha=.45,lw=.25,zorder=0)
  for y in np.arange(50,110.01,5):ax.plot([128.25,198.25],[y,y],color='#b8c2ce',alpha=.45,lw=.25,zorder=0)
 else:
  image=board_artwork_canvas(CFG,'front' if side=='F' else 'back')
  if side=='B':image=image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  ax.imshow(image,extent=(128.25,198.25,110,50),origin='upper',zorder=6.5,clip_path=boardpatch)
 # Copper pours, traces and vias use their actual coordinates and dimensions.
 for zone in kids(board,'zone'):
  if layer(zone)!=side+'.Cu': continue
  for p in kids(zone,'filled_polygon'):
   pts=get(p,'pts')
   if pts:
    verts=[list(map(float,v[1:3])) for v in pts if v[0]=='xy']
    if not template:ax.add_patch(Polygon(verts,fc=np.array(CFG['board']['rgb'])/255*.85,ec='none',zorder=2))
 seg=[]; widths=[]
 for line in kids(board,'segment'):
  if layer(line)==side+'.Cu':
   seg.append([xy(line,'start'),xy(line,'end')]); widths.append(float(get(line,'width')[0])*5)
 ax.add_collection(LineCollection(seg,colors='#b1b8c0' if template else np.minimum(1,np.array(CFG['board']['rgb'])/255*1.3),linewidths=widths,zorder=3,capstyle='round'))
 for v in kids(board,'via'):
  p=xy(v,'at'); r=float(get(v,'size')[0])/2
  ax.add_patch(Circle(p,r,fc='#b9ab7d',ec='none',zorder=5))
  ax.add_patch(Circle(p,float(get(v,'drill')[0])/2,fc='#101923',ec='none',zorder=6))
 for f in footprints:
  at=get(f,'at'); origin=np.array(list(map(float,at[:2]))); angle=float(at[2]) if len(at)>2 else 0
  t=np.deg2rad(-angle); rot=np.array([[np.cos(t),-np.sin(t)],[np.sin(t),np.cos(t)]])
  def tf(p): return np.asarray(p)@rot.T+origin
  # Silkscreen and optional engineering outline for the display.
  for prim in [v for v in f if isinstance(v,list) and v[0] in ['fp_line','fp_rect','fp_circle','fp_arc','fp_poly']]:
   lay=layer(prim)
   if lay not in ({side+'.SilkS',side+'.Fab',side+'.CrtYd','Dwgs.User'} if template else {side+'.SilkS'}): continue
   typ=prim[0]
   if typ=='fp_line': pts=np.array([xy(prim,'start'),xy(prim,'end')])
   elif typ=='fp_rect':
    a,b=xy(prim,'start'),xy(prim,'end'); pts=np.array([a,[b[0],a[1]],b,[a[0],b[1]],a])
   elif typ=='fp_arc': pts=arcpts(prim)
   elif typ=='fp_poly': pts=np.array([list(map(float,v[1:3])) for v in get(prim,'pts')])
   else:
    c=xy(prim,'center'); r=np.linalg.norm(xy(prim,'end')-c); ts=np.linspace(0,2*np.pi,64); pts=c+r*np.column_stack([np.cos(ts),np.sin(ts)])
   pts=tf(pts); ax.plot(pts[:,0],pts[:,1],color='#42566a' if template else '#cfdfce',lw=.5 if template else .65,zorder=7)
  for pad in kids(f,'pad'):
   layers=get(pad,'layers'); through=pad[2] in ['thru_hole','np_thru_hole']
   if not through and side+'.Cu' not in layers: continue
   pos=xy(pad,'at'); size=xy(pad,'size'); pa=get(pad,'at'); pang=float(pa[2]) if len(pa)>2 else angle
   # KiCad stores the pad orientation relative to the board.
   padang=np.deg2rad(-pang); pr=np.array([[np.cos(padang),-np.sin(padang)],[np.sin(padang),np.cos(padang)]])
   center=tf(pos)
   shape=pad[3]
   if shape=='circle':
    ax.add_patch(Circle(center,size[0]/2,fc='#d2b874' if pad[2]!='np_thru_hole' else '#2c6a58',ec='none',zorder=8))
   else:
    w,h=size
    if shape in ['oval','roundrect']:
     rad=min(w,h)/2 if shape=='oval' else min(w,h)*float(get(pad,'roundrect_rratio',['.25'])[0])
     ps=[]
     for cx,cy,st in [(w/2-rad,h/2-rad,0),(-w/2+rad,h/2-rad,90),(-w/2+rad,-h/2+rad,180),(w/2-rad,-h/2+rad,270)]:
      a=np.deg2rad(np.linspace(st,st+90,9)); ps.extend(np.column_stack([cx+rad*np.cos(a),cy+rad*np.sin(a)]))
     ps=np.array(ps)
    else: ps=np.array([[-w/2,-h/2],[w/2,-h/2],[w/2,h/2],[-w/2,h/2]])
    ax.add_patch(Polygon(ps@pr.T+center,fc='#d2b874',ec='none',zorder=8))
   drill=get(pad,'drill')
   if drill:
    nums=[float(v) for v in drill if isinstance(v,str) and re.fullmatch(r'[\d.]+',v)]
    if nums: ax.add_patch(Circle(center,nums[0]/2,fc='#111a26',ec='#839084',lw=.3,zorder=9))
  # Reference labels for components visible on this face.
  if layer(f)==side+'.Cu':
   ref=prop(f,'Reference')
   if ref.startswith('SW') and 'Hotswap' in f[1]:
    ax.text(origin[0],origin[1]+6.2,ref,color='#24394d' if template else '#ebeddd',fontsize=4 if template else 7,ha='center',zorder=11)
   elif ref in ['U1','U2','J1']:
    ax.text(origin[0],origin[1]-2,ref,color='#24394d' if template else '#ebeddd',fontsize=4 if template else 7,ha='center',zorder=11)
 # Actual board edge, including the USB cutout inside J1.
 for obj in kids(board,'gr_line')+kids(board,'gr_arc'):
  if layer(obj)=='Edge.Cuts':
   ps=arcpts(obj) if obj[0]=='gr_arc' else np.array([xy(obj,'start'),xy(obj,'end')]); ax.plot(ps[:,0],ps[:,1],color='#9bbca5',lw=.7,zorder=12)
 if template:
  ax.set_xlim((128.25,198.25) if side=='F' else (198.25,128.25));ax.set_ylim(110,50)
 else:ax.text(.5,1.035,'FRONT · USB at top' if side=='F' else 'BACK · USB at top',transform=ax.transAxes,color='#91a4b4',fontsize=10,ha='center',fontweight='bold')
 return ax

def templates():
 out=DESIGN/'templates';out.mkdir(parents=True,exist_ok=True)
 dpi=CFG['print']['dpi'];board_size=(round(70/25.4*dpi),round(60/25.4*dpi))
 for side,name in [('F','front'),('B','back')]:
  fig=plt.figure(figsize=(board_size[0]/dpi,board_size[1]/dpi),dpi=dpi);ax=fig.add_axes([0,0,1,1])
  render(ax,side,template=True)
  fig.savefig(out/f'board-{name}-guides.png',dpi=dpi,transparent=True)
  plt.close(fig)
  Image.new('RGBA',board_size).save(out/f'board-{name}-blank.png',dpi=(dpi,dpi))
 px=round(14.64/25.4*dpi);margin=round(CFG['print']['safe_margin_mm']/25.4*dpi)
 im=Image.new('RGBA',(px,px));draw=ImageDraw.Draw(im)
 draw.rectangle((1,1,px-2,px-2),outline='#426f9c',width=2)
 draw.rectangle((margin,margin,px-margin-1,px-margin-1),outline='#c9812a',width=2)
 draw.line((px//2,0,px//2,px),fill='#b6c2cd');draw.line((0,px//2,px,px//2),fill='#b6c2cd')
 im.save(out/'keycap-guides.png',dpi=(dpi,dpi));Image.new('RGBA',(px,px)).save(out/'keycap-blank.png',dpi=(dpi,dpi))
 print('Artist PNG templates saved in appearance/templates/.')

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--templates-only',action='store_true');args=parser.parse_args()
 templates()
 if not args.templates_only:
  fig,axs=plt.subplots(1,2,figsize=(16,8.8),facecolor='#111a26')
  fig.subplots_adjust(left=.04,right=.96,top=.94,bottom=.06,wspace=.1)
  for ax,side in zip(axs,['F','B']):render(ax,side)
  fig.savefig(BUILD/'board/macropad-preview.png',dpi=160,facecolor=fig.get_facecolor())
  fig.savefig(BUILD/'board/macropad-preview.svg',facecolor=fig.get_facecolor());plt.close(fig)
  print('Configured front/back PCB preview saved.')
