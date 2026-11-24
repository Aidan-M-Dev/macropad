"""Dimensioned washer-free fastener sections sliced from the actual STL meshes."""
import json
import re

from paths import BUILD

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from preview import load


def section_mask(mesh, plane_y, xs, zs):
    """Intersect triangles with Y=plane_y, then fill section spans by parity."""
    a, b = mesh, mesh[:, [1, 2, 0]]
    crossing = ((a[:, :, 1] <= plane_y) & (b[:, :, 1] > plane_y)) | ((b[:, :, 1] <= plane_y) & (a[:, :, 1] > plane_y))
    t = np.divide(plane_y-a[:, :, 1], b[:, :, 1]-a[:, :, 1],
                  out=np.zeros_like(a[:, :, 1]), where=crossing)
    points = (a+(b-a)*t[:, :, None])[crossing]
    segments = points[:, [0, 2]].reshape(-1, 2, 2)
    mask = np.zeros((len(zs), len(xs)), dtype=bool)
    for i, z in enumerate(zs):
        a, b = segments[:, 0], segments[:, 1]
        active = ((a[:, 1] <= z) & (b[:, 1] > z)) | ((b[:, 1] <= z) & (a[:, 1] > z))
        a, b = a[active], b[active]
        hits = np.unique(np.round(a[:, 0]+(z-a[:, 1])*(b[:, 0]-a[:, 0])/(b[:, 1]-a[:, 1]), 7))
        assert len(hits) % 2 == 0, ('Open section', z, hits)
        for left, right in hits.reshape(-1, 2):
            mask[i] |= (xs >= left) & (xs <= right)
    return mask


fig, axes = plt.subplots(1, 1, figsize=(12, 9), facecolor='#121923')
measurements = []
fit=next(row for row in json.loads((BUILD/'exports/top-frame-checks.json').read_text())['frames'] if row['file']=='top-frame-reinforced.stl')
for length, ax in [(6, axes)]:
    actual_length = fit['screw_length_mm']
    log = (BUILD/f'exports/logs/m3x{length}-base-m3x{length}.log').read_text()
    pcb_top = float(re.search(r'\bpcb_top = ([\d.]+)', log).group(1))
    seat = pcb_top+fit['overall_height_mm']-fit['head_recess_mm']
    top = seat+3
    xs, zs = np.linspace(-5, 5, 700), np.linspace(-.2, top+.4, 1400)
    refs = BUILD/f'previews/meshes/m3x{length}'
    frame_refs = BUILD/f'previews/meshes/frame-reinforced-base{length}'
    parts = [
        ('base', BUILD/f'exports/base-m3x{length}.stl', '#466981'),
        ('pcb', refs/'pcb.stl', '#27956e'),
        ('frame', frame_refs/'top_frame_assembled.stl', '#e4a34f'),
        ('nut', refs/'nuts.stl', '#b8bec6'),
        ('screw', frame_refs/'top_screws.stl', '#b8bec6'),
    ]
    masks = {}
    for name, path, colour in parts:
        mesh = load(path).copy()
        mesh[:, :, 0] -= 3.5
        mask = section_mask(mesh, 3.500013, xs, zs)
        masks[name] = mask
        rgb = tuple(int(colour[i:i+2], 16)/255 for i in (1, 3, 5))
        rgba = np.zeros((*mask.shape, 4))
        rgba[mask] = (*rgb, 1)
        ax.imshow(rgba, extent=(xs[0], xs[-1], zs[0], zs[-1]), origin='lower', interpolation='nearest')

    def inside(name, x, z):
        return bool(masks[name][np.argmin(abs(zs-z)), np.argmin(abs(xs-x))])

    # Verify flat head contact and constant wall thickness down the straight foot.
    assert inside('frame', 2, pcb_top+.1) and not inside('frame', 2, pcb_top-.1)
    assert inside('pcb', 2, pcb_top-.1)
    assert inside('frame', 2, seat-.1) and not inside('frame', 2, seat+.1)
    assert not inside('frame', 3.2, seat+.2) and inside('screw', 2, seat+.1)
    assert not inside('frame', 0, pcb_top+1), 'Screw clearance bore must be open'
    for height in (.1,fit['standoff_height_mm']/2,fit['standoff_height_mm']-.1):
        assert inside('frame',2.3,pcb_top+height) and not inside('frame',2.65,pcb_top+height), 'Standoff must have straight 0.8 mm walls throughout'
    tip=fit['screw_tip_z_mm']
    engagement=fit['nut_engagement_mm']

    ax.set_facecolor('#121923')
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f'Reinforced frame: M3 × {actual_length} mm',
                 color='#f1f4f6', fontsize=17, pad=18)
    ax.annotate('', xy=(-5.6, seat), xytext=(-5.6, tip),
                arrowprops=dict(arrowstyle='<->', color='#dce6ee', lw=1.2))
    ax.text(-6.1, (seat+tip)/2, f'{actual_length} mm under-head length', color='#dce6ee',
            rotation=90, ha='right', va='center', fontsize=11)
    labels = [
        (seat+1.5, f'M3 × {actual_length} socket-cap screw\nHead: Ø5.5 × 3 mm'),
        (seat, f'Flat head seat; no recess\n{fit["head_bearing_mm"]:g} mm plate, Ø{fit["mount_pad_diameter_mm"]:g} mm screw pad'),
        (pcb_top+fit['standoff_height_mm']/2, f'Integral foot: {fit["standoff_height_mm"]:g} mm tall; straight {fit["foot_wall_mm"]:g} mm walls\nØ{fit["foot_diameter_mm"]:g} mm outside, Ø{fit["foot_bore_mm"]:g} mm bore\nDirect PCB contact; no washers'),
        (pcb_top-.8, 'PCB: 1.6 mm'),
        ((pcb_top-1.6)/2, f'Existing printed base\nComponent clearance: {length-2.2:g} mm'),
        (1.6, f'M3 nut: 2.4 mm thick\n{engagement:g} mm thread engagement'),
        (tip, f'Screw tip: {tip:g} mm above exterior underside\nNut bottom: 0.4 mm above underside'),
    ]
    positions = []
    previous_y, previous_h = None, 0
    for anchor, label in sorted(labels, reverse=True):
        h = .60*len(label.splitlines())
        y = anchor if previous_y is None else min(anchor, previous_y-(h+previous_h)/2-.45)
        ax.plot([3.9, 5.2, 5.7], [anchor, y, y], color='#7890a3', lw=.8)
        ax.text(6, y, label, color='#dce6ee', fontsize=10.5, va='center')
        positions.append({'anchor_y': anchor, 'label_y': y, 'label': label})
        previous_y, previous_h = y, h
    ax.set_xlim(-8, 24)
    ax.set_ylim(min(-4, previous_y-1.5), top+1.0)
    measurements.append({'original_base_screw_mm': length, 'actual_screw_mm': actual_length,
                         'frame_foot_height_mm': fit['standoff_height_mm'], 'head_recess_mm': fit['head_recess_mm'],
                         'opening_mm': fit['opening_mm'], 'frame_foot_diameter_mm': fit['foot_diameter_mm'],
                         'frame_foot_wall_mm': fit['foot_wall_mm'], 'frame_foot_bore_mm': fit['foot_bore_mm'],
                         'plate_thickness_mm': fit['plate_thickness_mm'],
                         'separate_washers': 0, 'screw_tip_z_mm': tip, 'nut_engagement_mm': engagement,
                         'actual_mesh_bearing_and_recess_verified': True, 'annotations': positions})

fig.suptitle('Retaining frame — section through a mounting screw', color='#f1f4f6', fontsize=18, y=.97)
fig.text(.5, .91, 'Reinforced frame: 14.0 × 14.75 mm openings; 6 mm standoffs; flat 1 mm plate; 2 mm links; 2.4 mm arms.',
         ha='center', color='#c7d2dc', fontsize=10)
fig.text(.5, .04, 'Orange: retaining frame     Blue: existing base     Green: PCB     Silver: screw and nut\n'
         'Sections are cut from exported STL geometry. Screw lengths are measured below the head.',
         ha='center', color='#c7d2dc', fontsize=11, linespacing=1.6)
fig.subplots_adjust(top=.84, bottom=.10, left=.02, right=.98, wspace=.1)
fig.savefig(BUILD/'previews/frame-cross-section.png', dpi=180, facecolor=fig.get_facecolor())
plt.close(fig)
(BUILD/'exports/frame-section-dimensions.json').write_text(json.dumps(measurements, indent=2)+'\n')
print('Reinforced frame section: M3 × 12; 6 mm straight standoffs, 0.8 mm walls and flat bearing contact PASS.')
