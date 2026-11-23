"""Render board geometry directly from the supplied KiCad file, without KiCad."""
import re, math, json
from paths import BUILD, PCB
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
for f in footprints: print(prop(f,'Reference'),prop(f,'Value'),layer(f),get(f,'at'))

def render(ax,side):
 ax.set_facecolor('#111a26'); ax.set_aspect('equal'); ax.axis('off')
 ax.set_xlim(121,206); ax.set_ylim(117,43)
 if side=='B': ax.invert_xaxis()
 boardpatch=FancyBboxPatch((128.25,50),70,60,boxstyle='round,pad=0,rounding_size=1',fc='#123c37',ec='#7aab95',lw=1.2,zorder=1)
 ax.add_patch(boardpatch)
 # Copper pours, traces and vias use their actual coordinates and dimensions.
 for zone in kids(board,'zone'):
  if layer(zone)!=side+'.Cu': continue
  for p in kids(zone,'filled_polygon'):
   pts=get(p,'pts')
   if pts:
    verts=[list(map(float,v[1:3])) for v in pts if v[0]=='xy']
    ax.add_patch(Polygon(verts,fc='#194b42',ec='none',zorder=2))
 seg=[]; widths=[]
 for line in kids(board,'segment'):
  if layer(line)==side+'.Cu':
   seg.append([xy(line,'start'),xy(line,'end')]); widths.append(float(get(line,'width')[0])*5)
 ax.add_collection(LineCollection(seg,colors='#388b75',linewidths=widths,zorder=3,capstyle='round'))
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
   if lay!=side+'.SilkS': continue
   typ=prim[0]
   if typ=='fp_line': pts=np.array([xy(prim,'start'),xy(prim,'end')])
   elif typ=='fp_rect':
    a,b=xy(prim,'start'),xy(prim,'end'); pts=np.array([a,[b[0],a[1]],b,[a[0],b[1]],a])
   elif typ=='fp_arc': pts=arcpts(prim)
   elif typ=='fp_poly': pts=np.array([list(map(float,v[1:3])) for v in get(prim,'pts')])
   else:
    c=xy(prim,'center'); r=np.linalg.norm(xy(prim,'end')-c); ts=np.linspace(0,2*np.pi,64); pts=c+r*np.column_stack([np.cos(ts),np.sin(ts)])
   pts=tf(pts); ax.plot(pts[:,0],pts[:,1],color='#cfdfce',lw=.65,zorder=7)
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
    ax.text(origin[0],origin[1]+6.2,ref,color='#ebeddd',fontsize=7,ha='center',zorder=11)
   elif ref in ['U1','U2','J1']:
    ax.text(origin[0],origin[1]-2,ref,color='#ebeddd',fontsize=7,ha='center',zorder=11)
 # Actual board edge, including the USB cutout inside J1.
 for obj in kids(board,'gr_line')+kids(board,'gr_arc'):
  if layer(obj)=='Edge.Cuts':
   ps=arcpts(obj) if obj[0]=='gr_arc' else np.array([xy(obj,'start'),xy(obj,'end')]); ax.plot(ps[:,0],ps[:,1],color='#9bbca5',lw=.7,zorder=12)
 ax.text(.5,1.035,'FRONT' if side=='F' else 'BACK · mirrored',transform=ax.transAxes,color='#91a4b4',fontsize=10,ha='center',fontweight='bold')
 return ax

fig,axs=plt.subplots(1,2,figsize=(16,8.8),facecolor='#111a26')
fig.subplots_adjust(left=.04,right=.96,top=.94,bottom=.06,wspace=.1)
for ax,side in zip(axs,['F','B']): render(ax,side)
fig.savefig(BUILD/'board/macropad-preview.png',dpi=160,facecolor=fig.get_facecolor())
fig.savefig(BUILD/'board/macropad-preview.svg',facecolor=fig.get_facecolor())
print('Preview saved')
