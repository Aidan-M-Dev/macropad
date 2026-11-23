"""Behaviour checks for key colours, image alpha/orientation, opacity ordering and print mapping."""
from pathlib import Path
import sys,tempfile,copy,json
import numpy as np
from PIL import Image
from appearance import load_config,artwork_canvas
from paths import BUILD
import preview
cfg=load_config();results=[]
with tempfile.TemporaryDirectory(prefix='macropad-art-') as tmp:
    tmp=Path(tmp)
    # An asymmetric RGBA image catches mirroring/rotation and transparent padding errors.
    pix=np.zeros((40,40,4),dtype=np.uint8)
    pix[4:20,4:20]=[255,0,0,255];pix[4:20,20:36]=[0,255,0,255]
    pix[20:36,4:20]=[0,0,255,255];pix[20:36,20:36]=[255,255,0,255]
    path=tmp/'corners.png';Image.fromarray(pix).save(path)
    test=copy.deepcopy(cfg);test['keycaps'][0]['image']=str(path)
    art=np.asarray(artwork_canvas(test['keycaps'][0],14.64,test))
    assert art[0,0,3]==0 and art[art.shape[0]//2,art.shape[1]//2,3]>250
    ys,xs=np.where(art[:,:,3]>0)
    assert xs.max()-xs.min()+1==round(12/25.4*cfg['print']['dpi']), 'Small images must scale to their requested physical width'
    rotated=copy.deepcopy(test['keycaps'][0]);rotated['rotation_deg']=45
    rotated_art=np.asarray(artwork_canvas(rotated,14.64,test))
    yy,xx=np.where(rotated_art[:,:,3]>0);margin=int(cfg['print']['safe_margin_mm']/25.4*cfg['print']['dpi'])
    assert min(xx.min(),yy.min())>=margin and max(xx.max(),yy.max())<rotated_art.shape[0]-margin
    rgb=[[240,40,40],[40,240,40],[40,40,240],[240,200,40],[200,40,240],[40,200,240]]
    for key,col in zip(test['keycaps'],rgb):key['rgb']=col
    items=preview.scene(config=test)
    caps=[i for i in items if i['name'].startswith('keycap-')]
    assert len(caps)==6
    for i,obj in enumerate(caps):
        assert np.array_equal(obj['rgb'],rgb[i])
        top=obj['mesh'].reshape(-1,3);top=top[np.isclose(top[:,2],preview.FACES[i]['z'])]
        assert np.allclose((top[:,:2].min(0)+top[:,:2].max(0))/2,preview.CENTRES[i])
    results.append({'six_independent_rgb_assignments_and_correct_cap_centres':True})

    # Small deterministic render, with lighting direction matching the plane normal.
    preview.W=240;preview.H=240
    ids=np.array([[0,1,2],[0,2,3]]);uv=np.array([[0,0],[1,0],[1,1],[0,1]])
    def plane(z):return np.array([[-10,10,z],[10,10,z],[10,-10,z],[-10,-10,z]])[ids]
    bg=preview.item('body',plane(0),[230,220,200])
    decal=preview.item('artwork',plane(.01),[255,255,255],texture=pix.astype(np.float32),uv=uv[ids])
    out=tmp/'image.png';preview.render([bg,decal],out,view=(0,0,100))
    image=np.asarray(Image.open(out));assert image[90,90,0]>240 and image[90,90,1]<10
    assert image[90,150,1]>240 and image[90,150,0]<10
    assert image[150,90,2]>240 and image[150,90,0]<10
    assert image[150,150,0]>240 and image[150,150,1]>240
    # Transparent corner of decal shows the key body rather than a rectangular background.
    assert image[55,55,0]>image[55,55,2]>40
    results.append({'texture_uv_orientation_correct':True,'transparent_artwork_reveals_key_body':True})

    front=preview.item('red',plane(1),[255,0,0],.5)
    nearer=preview.item('blue',plane(2),[0,0,255],.5)
    p1=tmp/'alpha1.png';p2=tmp/'alpha2.png'
    preview.render([bg,front,nearer],p1,view=(0,0,100))
    preview.render([nearer,bg,front],p2,view=(0,0,100))
    assert np.array_equal(np.asarray(Image.open(p1)),np.asarray(Image.open(p2)))
    centre=np.asarray(Image.open(p1))[120,120];assert centre[2]>centre[0]>centre[1]
    foreground=preview.item('occluder',plane(3),[0,255,0])
    p3=tmp/'occluded.png';preview.render([bg,front,nearer,foreground],p3,view=(0,0,100))
    centre=np.asarray(Image.open(p3))[120,120];assert centre[1]>100 and centre[0]==0 and centre[2]==0
    results.append({'opacity_order_independent_per_pixel':True,'opaque_foreground_hides_transparent_parts_behind':True})

    bad=copy.deepcopy(cfg);bad['keycaps'][0]['rgb']=[256,0,0]
    p=tmp/'invalid.json';p.write_text(json.dumps(bad))
    try:load_config(p)
    except ValueError:pass
    else:raise AssertionError('Out of range RGB accepted')
    results.append({'invalid_rgb_rejected':True})
manifest=json.loads((BUILD/'print-pack/manifest.json').read_text())
assert [x['key'] for x in manifest['keys']]==[f'SW{i}' for i in range(1,7)]
for key,entry,face in zip(cfg['keycaps'],manifest['keys'],preview.FACES):
    assert entry['body_rgb']==key['rgb'] and entry['source_image']==key.get('image')
    expected=artwork_canvas(key,face['width_mm'],cfg)
    with Image.open(BUILD/'print-pack'/entry['artwork_png']) as art:
        assert np.array_equal(np.asarray(art.convert('RGBA')),np.asarray(expected))
    assert (BUILD/'print-pack'/entry['artwork_svg']).is_file()
# Identical artwork should share a file; distinct designs should remain independent.
canvases=[artwork_canvas(key,face['width_mm'],cfg).tobytes() for key,face in zip(cfg['keycaps'],preview.FACES)]
for i in range(6):
    for j in range(i):
        same_design=canvases[i]==canvases[j] and preview.FACES[i]['width_mm']==preview.FACES[j]['width_mm']
        assert (manifest['keys'][i]['artwork_png']==manifest['keys'][j]['artwork_png'])==same_design
png_names={p.name for p in (BUILD/'previews').glob('*.png')}
canonical={'top-frame-assembly.png','top-frame-without-keycaps.png','top-frame-exploded.png',
           'top-frame-top.png','top-frame-print.png','top-frame-comparison.png','frame-cross-section.png',
           'top-frame-reinforced-assembly.png','top-frame-reinforced-without-keycaps.png',
           'top-frame-reinforced-top.png','top-frame-reinforced-print.png','top-frame-reinforced-exploded.png'}
assert canonical<=png_names
assert png_names == canonical, ('Superseded renders remain', png_names-canonical)
sections=json.loads((BUILD/'exports/frame-section-dimensions.json').read_text())
assert len(sections)==1 and sections[0]['actual_screw_mm']==10
for section in sections:
    positions=section['annotations']
    assert section['separate_washers']==0 and section['actual_screw_mm']==section['original_base_screw_mm']+4
    assert any('no washers' in x['label'] for x in positions)
    for a,b in zip(positions,positions[1:]):
        assert a['label_y']-b['label_y'] >= .26*(len(a['label'].split('\n'))+len(b['label'].split('\n')))+.35-1e-6
results.append({'vendor_pack_matches_configured_artwork':True,'identical_artwork_deduplicated':True,'both_frame_version_views_present':True,'section_annotation_spacing':True})
(BUILD/'exports/appearance-checks.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'{len(results)} appearance, artwork, print-pack and annotation checks passed.')
