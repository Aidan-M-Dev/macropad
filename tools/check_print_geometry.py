"""Measure the exported meshes: flat floor, rounded underside and gradual nut roofs."""
import json,re
import numpy as np

from paths import BUILD, GENERATED
def load(path):
    return np.array(re.findall(r'vertex\s+([-+\deE.]+)\s+([-+\deE.]+)\s+([-+\deE.]+)',path.read_text()),dtype=float).reshape(-1,3,3)

def crossings(mesh,y,z):
    """Intersect an X-directed ray with the actual triangles at fixed Y/Z."""
    a=mesh[:,0];b=mesh[:,1]-a;c=mesh[:,2]-a
    det=b[:,1]*c[:,2]-b[:,2]*c[:,1]
    valid=np.abs(det)>1e-10
    a,b,c,det=a[valid],b[valid],c[valid],det[valid]
    u=((y-a[:,1])*c[:,2]-(z-a[:,2])*c[:,1])/det
    v=(b[:,1]*(z-a[:,2])-b[:,2]*(y-a[:,1]))/det
    valid=(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)
    return np.unique(np.round((a[:,0]+u*b[:,0]+v*c[:,0])[valid],5))

def inside(mesh,p,z):
    return bool(np.count_nonzero(crossings(mesh,p[1],z)>p[0])%2)

holes=np.array(json.loads((GENERATED/'pcb_geometry.json').read_text())['mount_holes'])
pairs=[(0,1),(1,3),(3,2),(2,0),(0,3),(1,2)]
results=[]
for length in [6]:
    path=BUILD/f'exports/base-m3x{length}.stl'
    mesh=load(path)
    assert np.allclose(crossings(mesh,30,3),[-1.15,-.35,70.35,71.15],atol=2e-5)
    # All six former rib paths must now be empty above the flat bottom skin.
    for i,j in pairs:
        a,b=holes[i],holes[j];t=1/3 if (i,j) in pairs[-2:] else .5
        p=(1-t)*a+t*b
        normal=np.array([-(b-a)[1],(b-a)[0]])/np.linalg.norm(b-a)
        assert not inside(mesh,p,1.3),(path.name,'remaining rib',i,j)
        for sign in [-1,1]:
            assert not inside(mesh,p+sign*.35*normal,1.3),(path.name,'remaining rib',i,j)
            assert not inside(mesh,p+sign*.45*normal,1.3),(path.name,'wide rib',i,j)
    assert inside(mesh,[35,15],.3) and not inside(mesh,[35,15],.5)
    for x in [10,20,35,50,60]:
        for y in [10,20,30,40,50]:assert not inside(mesh,[x,y],1.3),(path.name,'floor is not flat',x,y)
    # The exterior grows smoothly from its inset foot to the full-width wall.
    lower_x=[crossings(mesh,30,z)[0] for z in [.01,.1,.3,.6,1]]
    assert lower_x[0]>-.8 and np.all(np.diff(lower_x)<=2e-5)
    assert np.isclose(lower_x[-1],-1.15,atol=2e-5)
    diagonal=mesh.copy()
    diagonal[:,:,0]=(mesh[:,:,0]+mesh[:,:,1])/np.sqrt(2)
    diagonal[:,:,1]=(-mesh[:,:,0]+mesh[:,:,1])/np.sqrt(2)
    assert crossings(diagonal,0,.05)[0]>crossings(diagonal,0,3)[0]+.5,'Bottom corner was not rounded more broadly'
    corner_hits=crossings(diagonal,0,.6)
    assert corner_hits[1]-corner_hits[0]>=.75,'Rounded corner wall became too thin'
    local=mesh-np.array([*holes[0],0])
    pocket_z=2.5
    hits=crossings(local,0,pocket_z);positive=hits[hits>0]
    assert np.isclose(positive[0]*2,5.7,atol=2e-5),(path.name,'nut pocket across flats',positive)
    assert np.isclose(positive[1]-positive[0],.8,atol=2e-5),(path.name,positive)
    item={'file':path.name,'case_wall_mm':.8,'bottom_skin_mm':.4,'ribs_removed':True,'rounded_underside':True,'broader_bottom_corners':True,'nut_pocket_af_mm':5.7,'pocket_wall_mm':.8}
    if length==12:
        hits=crossings(local,0,8);positive=hits[hits>0]
        assert np.allclose(positive[:2],[1.7,2.5],atol=2e-5)
    worst=0
    for angle in [0,np.pi/6]:
        rotated=local.copy()
        rotated[:,:,0]=local[:,:,0]*np.cos(angle)+local[:,:,1]*np.sin(angle)
        rotated[:,:,1]=-local[:,:,0]*np.sin(angle)+local[:,:,1]*np.cos(angle)
        radii=[]
        for z in list(np.arange(2.7,4.11,.2))+[4.19]:
            hits=crossings(rotated,0,z);radii.append(hits[hits>0][0])
        inward=-np.diff(radii)
        assert np.all(inward>=-2e-5) and np.max(inward)<.4
        assert np.isclose(radii[-1],1.7,atol=.012)
        worst=max(worst,float(np.max(inward)))
    item.update(tube_wall_mm=.8,gradual_hex_to_bore=True,max_inward_step_per_02mm_layer_mm=round(worst,4))
    results.append(item)
washer=load(BUILD/'exports/accessories/washer-0.6mm.stl')
assert np.allclose(crossings(washer,0,.5),[-2.5,-1.7,1.7,2.5],atol=2e-5)
# The washer-set export intentionally contains four separate printable rings.
washer_set=load(BUILD/'exports/accessories/washers-0.6mm.stl')
assert np.isclose(washer[:,:,2].min(),0) and np.isclose(washer[:,:,2].max(),.6)
assert np.isclose(washer_set[:,:,2].min(),0) and np.isclose(washer_set[:,:,2].max(),.6)
assert len(washer_set)==4*len(washer)
# Measure the USB opening and its continuous roof in each version.
for length in [6]:
    mesh=load(BUILD/f'exports/base-m3x{length}.stl')
    # Rotate XY so our X-directed ray measures the rear wall along the connector centre.
    rotated=mesh.copy();rotated[:,:,0]=mesh[:,:,1];rotated[:,:,1]=mesh[:,:,0]
    pcb_bottom=length-1.8
    assert not inside(rotated,[60.7,44.75],pcb_bottom-3.5)
    assert not inside(rotated,[60.7,44.75+5.1],pcb_bottom-1)
    assert inside(rotated,[60.7,44.75+5.3],pcb_bottom-1)
    # Cast a vertical ray through the port centre to measure the actual roof.
    vertical=mesh[:,:,[2,0,1]]
    roof=crossings(vertical,44.75,60.7)[-2:]
    assert np.allclose(roof,[length-1.8,length+2],atol=2e-5),(length,'USB bridge',roof)
    assert np.isclose((length+1.2)-roof[0],3.0), 'USB ceiling must be exactly 3 mm lower'
    # The bottom stays at Z=0.4. The lowered ceiling is square across its width,
    # preserving connector clearance at the upper corners as well as the centre.
    floor_top=crossings(vertical,44.75,60.7)[1]
    assert np.isclose(floor_top,length-5.6,atol=2e-5),('USB bottom moved',floor_top)
    for dx in [-5.1,0,5.1]:
        assert not inside(rotated,[60.7,44.75+dx],pcb_bottom-.05)
        assert inside(rotated,[60.7,44.75+dx],pcb_bottom+.05)
# Measure the level rim and full-screen-width shelf, including slope and header relief.
for length in [6]:
    mesh=load(BUILD/f'exports/base-m3x{length}.stl');pcb_top=length-.2
    assert np.isclose(mesh[:,:,2].max(),pcb_top+2.2)
    for point in [[35,-.75],[-.75,30],[70.75,30],[30,60.75]]:
        assert inside(mesh,point,pcb_top+2.15),(length,'rim too low',point)
        assert not inside(mesh,point,pcb_top+2.25),(length,'rim too high',point)
    assert inside(mesh,[58,58.9],pcb_top+2.15)
    assert not inside(mesh,[58,58.9],pcb_top+2.25)
    assert not inside(mesh,[58,58.9],pcb_top+.2)
    front=60.35-1.7/np.tan(np.deg2rad(30))
    assert not inside(mesh,[58,front+.06],pcb_top+2.1)
    assert inside(mesh,[58,front+.3],pcb_top+2.1)
    for x in [22.3,23.75,35,50,60.2]:
        assert inside(mesh,[x,59.1],pcb_top+2.15),(length,'missing rear screen support',x)
    shelf_edges=crossings(mesh,59.1,pcb_top+2.15)
    assert np.allclose(shelf_edges[(shelf_edges>0)&(shelf_edges<70)],[22.25,60.25],atol=2e-5)
    for x in [22.15,60.35]:
        assert not inside(mesh,[x,59.1],pcb_top+2.15),(length,'shelf extends past screen',x)
    assert not inside(mesh,[23.75,58.5],pcb_top+2.15),'OLED header relief blocked'
    for x in [3.5,66.5]:
        assert not inside(mesh,[x,58.5],pcb_top+2.15),'Rear screw head relief blocked'
    along_y=mesh.copy();along_y[:,:,0]=mesh[:,:,1];along_y[:,:,1]=mesh[:,:,0]
    ramp_fronts=[]
    for z in [pcb_top+.6,pcb_top+1.4]:
        hits=crossings(along_y,58,z);ramp_fronts.append(hits[hits>50][0])
    measured_slope=np.rad2deg(np.arctan2(.8,ramp_fronts[0]-ramp_fronts[1]))
    assert np.isclose(measured_slope,30,atol=.01),(length,'shelf slope',measured_slope)
    results.append({'file':f'base-m3x{length}.stl','uniform_rim_height_above_pcb_mm':2.2,'screen_shelf_height_above_pcb_mm':2.2,'screen_shelf_width_mm':38,'shelf_ends_match_screen_bounds':True,'full_rear_screen_edge_supported':True,'header_clearance_and_rear_screw_access_verified':True,'screen_shelf_slope_degrees_from_bed':round(float(measured_slope),3),'screen_gap_mm':.3,'chamfered_slide_entry':True,'pcb_space_below_shelf_verified':True})
# Measure each labelled nut pocket, confirming the coupon reproduces the real fit.
coupon=load(BUILD/'exports/accessories/nut-fit-test-m3.stl')
for i,af in enumerate([5.45,5.5,5.6,5.7,5.8,5.85]):
    local=coupon-np.array([6+11*i,11,0])
    hits=crossings(local,0,1.5);positive=hits[hits>0]
    assert np.isclose(positive[0]*2,af,atol=2e-5)
    assert np.isclose(positive[1]-positive[0],.8,atol=2e-5)
    # Same wide mouth, seating height and screw bore as the case.
    mouth=crossings(local,0,.05);mouth=mouth[mouth>0]
    assert mouth[0]>positive[0]+.15
    roof=crossings(local,0,4.19);roof=roof[roof>0]
    assert np.isclose(roof[0],1.7,atol=.012)
assert np.allclose(coupon.reshape(-1,3).min(0),[0,0,0])
assert np.allclose(coupon.reshape(-1,3).max(0),[66,16,4.2])
results.append({'file':'nut-fit-test-m3.stl','pocket_af_sizes_mm':[5.45,5.5,5.6,5.7,5.8,5.85],'same_pocket_walls_leadin_and_roof_as_case':True})
results.append({'file':'washers-0.6mm.stl','washer_height_mm':.6,'washer_count':4,'on_print_bed':True})
results.append({'usb_opening_width_mm':10.4,'usb_opening_height_mm':3.8,'usb_opening_bottom_z_mm':.4,
                'usb_opening_top_z_mm':4.2,'usb_top_reduction_mm':3.0,'usb_bridge_thickness_mm':3.8,
                'nominal_clearance_above_connector_mm':0.0,'flat_upper_corners_verified':True,
                'under_board_connector_clearance_verified':True,'continuous_usb_roof_measured_in_compact_base':True})
(BUILD/'exports/print-geometry-checks.json').write_text(json.dumps(results,indent=2)+'\n')
print('Compact base, screen shelf, M3 nut-fit coupon and 0.6 mm washers verified from actual STL sections.')
