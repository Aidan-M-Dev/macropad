"""Export the washer-free reinforced frame and verify the compact base assembly."""
import json
import os
import subprocess

from paths import BUILD, CASE

env = {**os.environ, 'QT_QPA_PLATFORM': 'offscreen'}
logs = BUILD / 'exports/logs'
logs.mkdir(parents=True, exist_ok=True)


def export(part, path, length=6, empty=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    result = subprocess.run([
        'openscad', '--hardwarnings', '-D', f'part="{part}"',
        '-D', f'screw_length={length}', '-D', 'with_top_frame=true',
        '-o', str(path), str(CASE / 'macropad_case.scad'),
    ], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (logs / f'frame-reinforced-base{length}-{part}.log').write_text(result.stdout)
    assert 'ERROR:' not in result.stdout and 'WARNING:' not in result.stdout, result.stdout
    if empty:
        assert 'Current top level object is empty.' in result.stdout and not path.exists(), result.stdout
    else:
        assert result.returncode == 0 and path.exists(), result.stdout
    return result.stdout


export('top_frame', BUILD / 'exports/top-frame-reinforced.stl')
print('Exported top-frame-reinforced', flush=True)

checks = []
for variant in ('frame-reinforced',):
    for length in (6,):
        refdir = BUILD / f'previews/meshes/{variant}-base{length}'
        for part in ('top_frame_assembled', 'top_screws'):
            export(part, refdir / f'{part}.stl', length)
        for check in ('electronics', 'base', 'hardware'):
            export(f'check_frame_{check}', BUILD / f'exports/check-{variant}-base{length}-{check}.stl', length, empty=True)
            checks.append({'variant': variant, 'base_original_screw_mm': length, 'intersection': check, 'empty': True})
            print(variant, 'clearance, base', length, check, 'PASS', flush=True)

# Reuse the project's mesh validator and renderer after baseline meshes exist.
from preview import load, validate
import numpy as np

report = {'frames': [], 'separate_washers': 0}
fits = {
    'top-frame-reinforced': {'variant': 'frame-reinforced', 'opening_mm': [14.0,14.75], 'standoff_height_mm': 6.0,
                  'overall_height_mm': 7.0, 'plate_thickness_mm': 1.0, 'screw_length_mm': 12, 'head_recess_mm': 0,
                  'foot_diameter_mm': 5.0, 'foot_bore_mm': 3.4, 'foot_wall_mm': .8, 'mount_pad_diameter_mm': 6.2,
                  'head_bearing_mm': 1.0, 'screw_tip_z_mm': .8,
                  'nut_engagement_mm': 2.0, 'link_width_mm': 2.0, 'arm_width_mm': 2.4},
}

# Measure aperture side faces in the exported mesh, independently of SCAD echoes.
centres = np.array(json.loads((BUILD / 'generated/pcb_geometry.json').read_text())['key_centres'])
for name in fits:
    path = BUILD / f'exports/{name}.stl'
    mesh = load(path)
    fit=fits[name]
    report['frames'].append({**validate(path),**fit})
    assert np.isclose(mesh[:, :, 2].min(), 0, atol=2e-5) and np.isclose(mesh[:, :, 2].max(), fit['overall_height_mm'], atol=2e-5)
    # In print orientation, each straight foot runs from the back of the
    # 1 mm plate up to its PCB-contact face. Measure every foot from the actual
    # STL sidewalls, independently of the source parameter and assembled datum.
    holes=json.loads((BUILD/'generated/pcb_geometry.json').read_text())['mount_holes']
    measured=[]
    for centre in holes:
        radius=np.linalg.norm(mesh[:,:,:2]-np.asarray(centre),axis=2)
        # ASCII STL coordinates are rounded to six significant digits: allow
        # 0.0001 mm radially at the far PCB mounts (coordinates around 60 mm).
        radial_tolerance=1e-4
        wall=np.all(np.isclose(radius,fit['foot_diameter_mm']/2,atol=radial_tolerance,rtol=0),axis=1)
        wall &= (mesh[:,:,2].min(1)>=fit['plate_thickness_mm']-2e-5)&(np.ptp(mesh[:,:,2],axis=1)>2e-5)
        assert np.any(wall),('Missing standoff outer wall',centre)
        points=mesh[wall].reshape(-1,3);zmin,zmax=points[:,2].min(),points[:,2].max()
        height=zmax-zmin
        assert np.isclose(height,6.0,atol=2e-5),('Standoff is not 6 mm tall',centre,height)
        assert np.isclose(zmin,fit['plate_thickness_mm'],atol=2e-5) and np.isclose(zmax,fit['overall_height_mm'],atol=2e-5)
        # Straight clearance bores reach the flat bed face, with no counterbores.
        bore=np.all(np.isclose(radius,fit['foot_bore_mm']/2,atol=radial_tolerance,rtol=0),axis=1)&(np.ptp(mesh[:,:,2],axis=1)>2e-5)
        assert np.any(bore) and np.allclose([mesh[bore,:,2].min(),mesh[bore,:,2].max()],[0,7])
        outer_radius=np.linalg.norm(points[:,:2]-centre,axis=1)
        inner_radius=radius[bore].reshape(-1)
        thickness=float(outer_radius.mean()-inner_radius.mean())
        assert np.isclose(thickness,.8,atol=2e-5),('Standoff wall is not 0.8 mm',centre,thickness)
        # No wider root or taper may be hidden among the foot sidewalls.
        local=np.all(radius<fit['mount_pad_diameter_mm']/2+2e-5,axis=1)
        sides=local & (mesh[:,:,2].min(1)>=fit['plate_thickness_mm']-2e-5)&(np.ptp(mesh[:,:,2],axis=1)>2e-5)
        assert np.all((wall|bore)[sides]),('Standoff has a taper or step',centre)
        measured.append({'centre_mm':centre,'height_mm':round(float(height),5),
                         'print_z_range_mm':[round(float(zmin),5),round(float(zmax),5)],
                         'outer_diameter_mm':round(float(2*outer_radius.mean()),5),
                         'bore_diameter_mm':round(float(2*inner_radius.mean()),5),
                         'wall_thickness_mm':round(thickness,5)})
    report['frames'][-1]['measured_standoffs']=measured
    print('Measured all four exported standoffs: 6.000 mm tall, straight 0.800 mm walls',flush=True)
    for cx, cy in centres:
        for axis, centre, other in ((0, cx, cy), (1, cy, cx)):
            for sign in (-1, 1):
                plane = centre + sign * fit['opening_mm'][axis]/2
                faces = mesh[np.all(np.isclose(mesh[:, :, axis], plane, atol=2e-5), axis=1)]
                faces = faces[np.all(np.abs(faces[:, :, 1-axis]-other)<=fit['opening_mm'][1-axis]/2+.0001, axis=1)]
                assert len(faces) >= 2, ('Missing aperture wall', name, cx, cy, axis, sign)
                assert np.isclose(np.ptp(faces[:, :, 2]), fit['plate_thickness_mm']), ('Wrong plate thickness', name, cx, cy)

    def check_strip(start,end,width):
        start,end=np.asarray(start),np.asarray(end)
        direction=end-start;length=np.linalg.norm(direction);direction=direction/length
        normal=np.array([-direction[1],direction[0]])
        along=(mesh[:,:,:2]-start)@direction
        across=(mesh[:,:,:2]-start)@normal
        for sign in (-1,1):
            # Diagonal capsule sides inherit the circle caps' polygon faceting.
            faces=np.all(np.isclose(across,sign*width/2,atol=.005),axis=1)
            faces &= (along.min(1)<=length/2)&(along.max(1)>=length/2)
            assert np.count_nonzero(faces)>=2,('Wrong reinforced strip width',start,end,width,sign)
            assert np.isclose(np.ptp(mesh[faces,:,2]),fit['plate_thickness_mm'])

    check_strip(centres[0],centres[1],fit['link_width_mm'])
    holes=json.loads((BUILD/'generated/pcb_geometry.json').read_text())['mount_holes']
    corner=centres[0]+np.array([-1,1])*(np.array(fit['opening_mm'])/2+.6)
    check_strip(holes[0],corner,fit['arm_width_mm'])

for fit in fits.values():
    length=6
    refs=BUILD/f'previews/meshes/{fit["variant"]}-base{length}'
    screws = load(refs/'top_screws.stl')
    assert np.isclose(screws[:, :, 2].min(), fit['screw_tip_z_mm']), 'Wrong screw tip position'
    assert np.isclose(np.ptp(screws[:, :, 2]), fit['screw_length_mm']+3), 'Wrong screw length'
    frame = load(refs/'top_frame_assembled.stl')
    pcb = load(BUILD / f'previews/meshes/m3x{length}/pcb.stl')
    assert np.isclose(frame[:, :, 2].min(), pcb[:, :, 2].max()), 'Feet must touch PCB directly'
    assert np.isclose(frame[:, :, 2].max()-(screws[:, :, 2].max()-3), fit['head_recess_mm']), 'Wrong head recess'
    # Measure the actual foot shoulder and diameter, below the plate.
    pcb_top=pcb[:,:,2].max();foot_top=pcb_top+fit['standoff_height_mm']
    nuts=load(BUILD/f'previews/meshes/m3x{length}/nuts.stl')
    engagement=nuts[:,:,2].max()-max(nuts[:,:,2].min(),screws[:,:,2].min())
    assert np.isclose(engagement,fit['nut_engagement_mm']), 'Wrong nut engagement'
    points=frame.reshape(-1,3)
    local=points[(np.abs(points[:,0]-3.5)<4)&(np.abs(points[:,1]-3.5)<4)]
    foot=local[local[:,2]<foot_top-.001]
    assert np.isclose(np.ptp(foot[:,0]),fit['foot_diameter_mm']), 'Wrong standoff diameter'
    assert np.any(np.isclose(local[:,2],foot_top)), 'Missing 6 mm standoff shoulder'

report.update(clearances=checks,
              physical_clone_clip_and_keycap_fit='Requires physical fit check; simplified electronics references only')
(BUILD / 'exports/top-frame-checks.json').write_text(json.dumps(report, indent=2)+'\n')
print('Frame mesh, apertures, screw lengths and clearances PASS', flush=True)
