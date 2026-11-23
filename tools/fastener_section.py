"""Dimensioned nut-fastener sections from each exported base's actual stack."""
from paths import BUILD
import re, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
from appearance import load_config
cfg=load_config(require_images=False)
base_colour=tuple(v/255 for v in cfg['case']['base']['rgb'])
def arr(log,name):return json.loads(re.search(r'\b'+name+r' = (\[[^\]]+\])',log).group(1))
for length in [6]:
    log=(BUILD/f'exports/logs/m3x{length}-base-m3x{length}.log').read_text()
    af,nh,pocket_af,pocket_top,tip,engagement=arr(log,'nut_stack')
    boss_height,tube_d,tube_height=arr(log,'nut_support')
    taper,seat_width,taper_af=arr(log,'nut_roof_taper')
    boss_wall,_,_=arr(log,'fastener_walls')
    entry_af,leadin=arr(log,'nut_entry')
    clearance,washer_d,nominal,hd,hh=arr(log,'fastener_radial')
    _,_,_,skin,_,_=arr(log,'print_dimensions')
    _,_,land=arr(log,'washer')
    socket_af,socket_depth=arr(log,'screw_drive')
    board_bottom=float(re.search(r'pcb_bottom = ([\d.]+)',log).group(1))
    board_top=float(re.search(r'\bpcb_top = ([\d.]+)',log).group(1))
    pcb=board_top-board_bottom;top_seat=board_top+land
    assert abs(pcb-1.6)<1e-6, 'PCB thickness parsed from wrong metadata field'
    fig,ax=plt.subplots(figsize=(12,10),facecolor='#121923');ax.set_facecolor('#121923')
    ax.set_aspect('equal');ax.set_xlim(-8,28);ax.axis('off')
    def rect(x,y,w,h,c):ax.add_patch(Rectangle((x,y),w,h,fc=c,ec='#121923',lw=.5))
    cr=clearance/2;wr=washer_d/2
    outer_entry=entry_af/2+boss_wall;outer_hex=pocket_af/2+boss_wall
    for a,b in [(-6,-outer_entry),(outer_entry,6)]:rect(a,0,b-a,skin,base_colour)
    profile=[(outer_entry,0),(outer_hex,leadin),(outer_hex,pocket_top),
             (tube_d/2,boss_height),(tube_d/2,board_bottom),(cr,board_bottom)]
    if taper:profile.extend([(cr,pocket_top+taper),(taper_af/2,pocket_top)])
    else:profile.append((cr,pocket_top))
    profile.extend([(pocket_af/2,pocket_top),(pocket_af/2,leadin),(entry_af/2,0)])
    for sign in [-1,1]:
        ax.add_patch(Polygon([(sign*x,y) for x,y in profile],closed=True,fc=base_colour,ec='#121923',lw=.5))
    for a,b in [(-wr,-cr),(cr,wr)]:rect(a,board_top,b-a,land,base_colour)
    for a,b in [(-6,-1.6),(1.6,6)]:rect(a,board_bottom,b-a,pcb,'#1d7e5b')
    for a,b in [(-af/2,-1.25),(1.25,af/2)]:rect(a,pocket_top-nh,b-a,nh,'#b8bec6')
    rect(-nominal/2,tip,nominal,length,'#b8bec6');rect(-hd/2,top_seat,hd,hh,'#b8bec6')
    rect(-socket_af/2,top_seat+hh-socket_depth,socket_af,socket_depth,'#121923')
    labels=[
        (top_seat+hh/2,f'M3 x {length} socket-cap screw'),
        (board_top+land/2,f'Insulating washer: {land:g} mm'),
        (board_bottom+pcb/2,f'PCB: {pcb:g} mm'),
        (board_bottom/2,f'PCB-to-floor space: {board_bottom-skin:g} mm\nRequired component envelope: 3.5 mm'),
        (pocket_top+taper/2,f'Sloped roof: {taper:g} mm; bearing ledge: {seat_width:g} mm'),
        (pocket_top-nh/2,f'M3 nut: {af:g} mm AF x {nh:g} mm\nPocket: {pocket_af:g} mm AF'),
        (tip,f'Nut bottom / screw tip: {tip:g} mm recessed\nFull nut engagement: {engagement:g} mm'),
        (0,f'Bottom skin: {skin:g} mm; nut inserts from below'),
    ]
    positions=[];previous_y=None;previous_h=0
    for anchor,text in sorted(labels,reverse=True):
        height=.52*len(text.split('\n'))
        y=anchor if previous_y is None else min(anchor,previous_y-(height+previous_h)/2-.35)
        ax.plot([6.3,7,7.4],[anchor,y,y],color='#6f8799',lw=.8)
        ax.text(7.7,y,text,color='#dce6ee',fontsize=10,va='center')
        positions.append({'anchor_y':anchor,'label_y':y,'label':text})
        previous_y=y;previous_h=height
    ax.set_ylim(min(-2,previous_y-1),top_seat+hh+1)
    fig.savefig(BUILD/f'previews/fastener-section-m3x{length}.png',dpi=160,facecolor=fig.get_facecolor(),bbox_inches='tight')
    plt.close(fig)
    (BUILD/f'exports/fastener-annotation-positions-m3x{length}.json').write_text(json.dumps(positions,indent=2)+'\n')
print('Legacy compact base section generated.')
