"""Export the compact nut-retained base, washers and exact CSG clearance checks."""
import subprocess, os, json, argparse
from appearance import load_config, sync_scad
sync_scad(load_config(require_images=False))
from paths import CASE as ROOT, BUILD
LENGTHS = (6,)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-only', action='store_true', help='Reuse unchanged washer and reference meshes')
args = parser.parse_args()
env = {**os.environ, 'QT_QPA_PLATFORM': 'offscreen'}
logs = BUILD/'exports/logs'
logs.mkdir(parents=True, exist_ok=True)

def run(part, path, length=6):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    cmd = ['openscad', '--hardwarnings', '-D', f'part="{part}"', '-D', f'screw_length={length}', '-D', 'with_top_frame=false', '-o', str(path), str(ROOT/'macropad_case.scad')]
    p = subprocess.run(cmd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (logs/f'm3x{length}-{path.stem}.log').write_text(p.stdout)
    return p

for length in LENGTHS:
    path = BUILD/f'exports/base-m3x{length}.stl'
    p = run('base', path, length)
    if p.returncode or 'ERROR:' in p.stdout or 'WARNING:' in p.stdout:
        raise RuntimeError(p.stdout)
    print('Exported', path.name, flush=True)
if not args.base_only:
    for part, name in [('washer', 'washer-0.6mm'), ('washer_set', 'washers-0.6mm'), ('nut_fit_test', 'nut-fit-test-m3')]:
        p = run(part, BUILD/f'exports/accessories/{name}.stl')
        if p.returncode:
            raise RuntimeError(p.stdout)
    for length in LENGTHS:
        refdir = BUILD/f'previews/meshes/m3x{length}'
        for part in ['washers', 'pcb', 'switches', 'keycaps', 'screen_board', 'screen_glass', 'screen_face', 'screen_contacts', 'screen_components', 'screen_headers', 'usb', 'top_screws', 'nuts']:
            p = run(part, refdir/(part+'.stl'), length)
            if p.returncode:
                raise RuntimeError(p.stdout)
        print('Reference meshes M3 x', length, flush=True)
results = []
for length in LENGTHS:
    for item in ['hardware_electronics', 'washers', 'pcb', 'screen', 'screen_insertion', 'keys', 'usb', 'underside', 'fasteners']:
        path = BUILD/f'exports/check-m3x{length}-{item}.stl'
        p = run('check_'+item, path, length)
        ok = ('Current top level object is empty.' in p.stdout and not path.exists()
              and 'ERROR:' not in p.stdout and 'WARNING:' not in p.stdout)
        results.append({'screw_length_mm': length, 'intersection': item, 'empty': ok})
        print('Clearance M3 x', length, item, 'PASS' if ok else 'FAIL', flush=True)
        if not ok:
            print(p.stdout)
(BUILD/'exports/clearance-checks.json').write_text(json.dumps(results, indent=2)+'\n')
if not all(r['empty'] for r in results):
    raise SystemExit('Clearance check failed')
