"""Verify compact screw selection, nut engagement and rejected unsafe settings."""
from pathlib import Path
import os, subprocess, json, re
import numpy as np
from paths import CASE as ROOT, ACCESSORIES, BUILD
env={**os.environ,'QT_QPA_PLATFORM':'offscreen'}
results=[]
def compile_case(name,params=(),expect=None,source=None):
    cmd=['openscad','--hardwarnings']
    for param in params:cmd+=['-D',param]
    path=Path(f'/tmp/macropad-param-{name}.echo')
    out=subprocess.run(cmd+['-o',str(path),str(source or ROOT/'macropad_case.scad')],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    log=path.read_text() if path.exists() else out.stdout
    ok=('ERROR: Assertion' in log and expect in log) if expect else (out.returncode==0 and 'ERROR:' not in log and 'WARNING:' not in log)
    assert ok,(name,log,out.stdout)
    results.append({'case':name,'expected':'rejected' if expect else 'compiled','passed':True})
    return log
for name,params,expect in [
    ('compact-m3x6',[],None),
    ('too-short-m3x4',['screw_length=4'],'Insufficient underside clearance'),
    ('no-washer',['washer_thickness=0'],'Insufficient washer thickness'),
    ('thin-washer',['washer_thickness=0.4'],'Insufficient washer thickness'),
    ('underside-clearance',['underside_clearance=4'],'Insufficient underside clearance'),
    ('rim-no-protection',['rim_above_pcb_top=0'],'Rim must protect PCB edge'),
    ('rim-keycap',['rim_above_pcb_top=3'],'Rim reaches pressed keycap'),
    ('rim-below-shelf',['rim_above_pcb_top=1'],'Rim must match screen shelf height'),
    ('tall-rib',['rib_enabled=true','rib_height_layers=20'],'Insufficient underside clearance'),
    ('thin-skin',['bottom_layers=1'],'at least two walls/skin layers'),
    ('thin-roof',['nut_roof_height=0.6'],'Insufficient bearing above nut pocket'),
    ('thick-roof-compact',['nut_roof_height=2.0'],'Insufficient bearing above nut pocket'),
    ('no-leadin',['nut_leadin=0'],'Invalid nut entry'),
    ('steep-taper',['nut_taper_height=0.4'],'Nut roof taper too steep'),
    ('taper-above-boss',['nut_taper_height=2'],'Nut roof taper must fit'),
    ('no-bearing-ledge',['nut_seat_width=0'],'Invalid nut bearing ledge'),
    ('narrow-usb',['usb_opening_width=9.8'],'Insufficient USB opening clearance'),
    ('deep-usb',['usb_body_height=4'],'USB opening cuts through bottom skin'),
    ('thin-usb-bridge',['usb_bridge_layers=1'],'USB bridge needs at least two layers'),
    ('blocked-usb',['usb_bridge_layers=20'],'Insufficient clearance above USB connector'),
    ('socket-through-head',['socket_depth=3'],'Invalid hex socket'),
    ('fine-layers',['layer_height=0.1'],None),
    ('shelf-too-high',['screen_shelf_height=2.5'],'clearance below screen'),
    ('shelf-tight-relief',['screen_shelf_clearance=0.1'],'insertion clearance around components'),
    ('shelf-invalid-slope',['screen_shelf_slope_angle=0'],'Invalid screen shelf slope angle'),
    ('shelf-no-entry',['screen_shelf_overlap=0.1'],'bearing area'),
    ('shelf-on-pcb',['screen_shelf_board_clearance=0'],'main PCB clear'),
    ('shelf-steep-overhang',['screen_shelf_overlap=4'],'overhang exceeds'),
    ('header-too-short',['screen_mount_gap=2'],'clearance below screen'),
]:compile_case(name,params,expect)
for mode in ['assembly','exploded','section','print','washer_set','nut_fit_test']:
    compile_case(mode,[f'part="{mode}"'])
for length in [6]:
    compile_case(f'base-wrapper-{length}',source=ROOT/f'base-m3x{length}.scad')
compile_case('nut-test-wrapper',source=ACCESSORIES/'nut-fit-test-m3.scad')
compile_case('washer-wrapper',source=ACCESSORIES/'washers-0.6mm.scad')
def arr(log,name):return json.loads(re.search(r'\b'+name+r' = (\[[^\]]+\])',log).group(1))
for length in [6]:
    log=(BUILD/f'exports/logs/m3x{length}-base-m3x{length}.log').read_text()
    af,nh,paf,seat,tip,engagement=arr(log,'nut_stack')
    boss,tube_d,tube_height=arr(log,'nut_support')
    size=arr(log,'case_size')
    assert np.allclose([tip,engagement,paf],[.4,2.4,5.7])
    assert np.isclose(size[2],length+2)
    overlap=59.29-(60.35-1.7/np.tan(np.deg2rad(30)))
    assert np.allclose(arr(log,'screen_shelf'),[2.2,2.5,.3,38,overlap])
    assert np.allclose(np.array(arr(log,'screen_shelf_bounds'))[[0,2]],[22.25,60.25])
    assert np.isclose(float(re.search(r'\bscreen_shelf_slope = ([\d.]+)',log).group(1)),30)
    assert np.isclose(float(re.search(r'\brim_above_pcb_top = ([\d.]+)',log).group(1)),2.2)
    assert np.allclose(arr(log,'washer'),[5,3.4,.6])
    assert np.allclose(arr(log,'nut_roof_taper'),[1.4,.25,5.2])
    assert np.allclose(arr(log,'usb_opening'),[10.4,6.8,length-5.6])
    assert np.allclose(arr(log,'usb_bridge'),[.8,length+1.2,length+2])
    assert np.allclose(arr(log,'print_dimensions'),[.4,.2,.8,.4,0,0])
    assert np.allclose(arr(log,'fastener_walls'),[.8,.8,.8])
    space=float(re.search(r'underside_space = ([\d.]+)',log).group(1))
    assert space>=3.5 and np.isclose(space,length-2.2)
    def bounds(name):
        text=(BUILD/f'previews/meshes/m3x{length}/{name}.stl').read_text()
        v=np.array(re.findall(r'vertex\s+([-+\deE.]+)\s+([-+\deE.]+)\s+([-+\deE.]+)',text),dtype=float)
        return v.min(0),v.max(0)
    low,high=bounds('top_screws')
    assert np.isclose(low[2],tip) and np.isclose(high[2]-low[2],length+3)
    low,high=bounds('usb')
    pcb_bottom=float(re.search(r'pcb_bottom = ([\d.]+)',log).group(1))
    assert np.isclose(high[2],pcb_bottom) and np.isclose(high[2]-low[2],3.5)
    assert np.isclose(high[0]-low[0],9.8)
    pcb_top=pcb_bottom+1.6
    low,high=bounds('screen_headers')
    assert np.isclose(low[2],pcb_top) and np.isclose(high[2]-low[2],2.5)
    low,high=bounds('screen_board')
    assert np.isclose(low[2],pcb_top+2.5)
    low,high=bounds('nuts')
    assert np.isclose(low[2],tip) and np.isclose(high[2]-low[2],2.4)
    results.append({'screw_length_mm':length,'case_height_mm':size[2],'underside_space_mm':space,'full_nut_engagement_mm':engagement,'screw_tip_recess_mm':tip,'nut_pocket_af_mm':paf,'under_board_usb_verified':True})
(BUILD/'exports/parameter-checks.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'{len(results)} parameter and hardware checks passed.')
