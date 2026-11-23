"""Export both washer-free MX frames and verify the compact base assembly."""
import json
import os
import subprocess

from paths import BUILD, CASE

env = {**os.environ, 'QT_QPA_PLATFORM': 'offscreen'}
logs = BUILD / 'exports/logs'
logs.mkdir(parents=True, exist_ok=True)


def export(part, path, length=6, empty=False, reinforced=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    result = subprocess.run([
        'openscad', '--hardwarnings', '-D', f'part="{part}"',
        '-D', f'screw_length={length}', '-D', 'with_top_frame=true',
        '-D', f'frame_reinforced={str(reinforced).lower()}',
        '-o', str(path), str(CASE / 'macropad_case.scad'),
    ], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    variant = 'frame-reinforced' if reinforced else 'frame'
    (logs / f'{variant}-base{length}-{part}.log').write_text(result.stdout)
    assert 'ERROR:' not in result.stdout and 'WARNING:' not in result.stdout, result.stdout
    if empty:
        assert 'Current top level object is empty.' in result.stdout and not path.exists(), result.stdout
    else:
        assert result.returncode == 0 and path.exists(), result.stdout
    return result.stdout


for part, name in [('top_frame', 'top-frame')]:
    export(part, BUILD / f'exports/{name}.stl')
    print('Exported', name, flush=True)
export('top_frame', BUILD / 'exports/top-frame-reinforced.stl', reinforced=True)
print('Exported top-frame-reinforced', flush=True)

checks = []
for reinforced in (False, True):
    variant = 'frame-reinforced' if reinforced else 'frame'
    for length in (6,):
        refdir = BUILD / f'previews/meshes/{variant}-base{length}'
        for part in ('top_frame_assembled', 'top_screws'):
            export(part, refdir / f'{part}.stl', length, reinforced=reinforced)
        for check in ('electronics', 'base', 'hardware'):
            export(f'check_frame_{check}', BUILD / f'exports/check-{variant}-base{length}-{check}.stl', length, empty=True, reinforced=reinforced)
            checks.append({'variant': variant, 'base_original_screw_mm': length, 'intersection': check, 'empty': True})
            print(variant, 'clearance, base', length, check, 'PASS', flush=True)

# Reuse the project's mesh validator and renderer after baseline meshes exist.
from preview import load, validate
import numpy as np

report = {'frames': [], 'separate_washers': 0}

# Measure aperture side faces in the exported mesh, independently of SCAD echoes.
centres = np.array(json.loads((BUILD / 'generated/pcb_geometry.json').read_text())['key_centres'])
for name in ('top-frame', 'top-frame-reinforced'):
    path = BUILD / f'exports/{name}.stl'
    mesh = load(path)
    report['frames'].append(validate(path))
    assert np.isclose(mesh[:, :, 2].min(), 0) and np.isclose(mesh[:, :, 2].max(), 5.0)
    for cx, cy in centres:
        for axis, centre, other in ((0, cx, cy), (1, cy, cx)):
            for sign in (-1, 1):
                plane = centre + sign * 7
                faces = mesh[np.all(np.isclose(mesh[:, :, axis], plane, atol=2e-5), axis=1)]
                faces = faces[np.all(np.abs(faces[:, :, 1-axis]-other)<=7.0001, axis=1)]
                assert len(faces) >= 2, ('Missing 14 mm aperture wall', name, cx, cy, axis, sign)
                assert np.isclose(np.ptp(faces[:, :, 2]), 1.6), ('Wrong clip land thickness', name, cx, cy)

for length in (6,):
    screws = load(BUILD / f'previews/meshes/frame-base{length}/top_screws.stl')
    assert np.isclose(screws[:, :, 2].min(), .4), 'Long screw protrudes through base'
    assert np.isclose(np.ptp(screws[:, :, 2]), length+4+3), 'Wrong screw length'
    frame = load(BUILD / f'previews/meshes/frame-base{length}/top_frame_assembled.stl')
    pcb = load(BUILD / f'previews/meshes/m3x{length}/pcb.stl')
    assert np.isclose(frame[:, :, 2].min(), pcb[:, :, 2].max()), 'Feet must touch PCB directly'
    assert np.isclose(frame[:, :, 2].max()-(screws[:, :, 2].max()-3), .4), 'Wrong head recess'

report.update(clearances=checks, aperture_mm=14, clip_land_mm=1.6,
              screws_by_original_base={'M3x6': 'M3x10'},
              head_recess_mm=0.4, frame_foot_height_mm=3.4,
              physical_clone_clip_and_keycap_fit='Requires physical fit check; simplified electronics references only')
(BUILD / 'exports/top-frame-checks.json').write_text(json.dumps(report, indent=2)+'\n')
print('Frame mesh, apertures, screw lengths and clearances PASS', flush=True)
