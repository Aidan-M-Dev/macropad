"""Behaviour checks for key colours, image alpha/orientation, opacity ordering and print mapping."""
from pathlib import Path
import sys,tempfile,copy,json
import numpy as np
from PIL import Image
from PIL import ImageDraw
from unittest.mock import patch
import appearance
from appearance import load_config,artwork_canvas,board_artwork_canvas,resolve_image
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
    test['keycaps'][0]['artwork_size_mm']=[12,12]
    test['print']['trim_transparent_padding']=True
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

    bad=copy.deepcopy(cfg);bad['keycaps'][0]['colour']='#GG0000'
    p=tmp/'invalid.json';p.write_text(json.dumps(bad))
    try:load_config(p)
    except ValueError:pass
    else:raise AssertionError('Out of range RGB accepted')
    results.append({'invalid_hex_colour_rejected':True})

    # The teammate edits hex colours and flips the PETG preset, without needing
    # to remove a hidden opacity value or edit RGB channels.
    from paths import DESIGN
    raw=json.loads((DESIGN/'config.json').read_text())
    raw['case']['base']={'colour':'#1234ab','material':'solid'}
    raw['case']['frame']={'colour':'#D7E1E4','material':'transparent_petg'}
    p=tmp/'materials.json';p.write_text(json.dumps(raw));materials=load_config(p)
    assert materials['case']['base']['rgb']==[18,52,171]
    assert materials['case']['base']['opacity']==1
    assert materials['case']['frame']['opacity']==.58 and materials['case']['frame']['frosted_blur_px']==4
    from preview_top_frame import frame_scene
    items=frame_scene(config=materials)
    base=next(o for o in items if o['name']=='base');frame=next(o for o in items if o['name']=='top-frame')
    assert np.array_equal(base['rgb'],[18,52,171]) and np.array_equal(frame['rgb'],[215,225,228])
    assert base['opacity']==1 and frame['opacity']==.58
    assert frame['layer_height_mm']==.2 and frame['frosted_blur_px']==4
    for field,value in [('colour','#XYZ123'),('material','glass'),('opacity',True)]:
        invalid=copy.deepcopy(raw);invalid['case']['frame'][field]=value
        p=tmp/'invalid-material.json';p.write_text(json.dumps(invalid))
        try:load_config(p)
        except ValueError:pass
        else:raise AssertionError(('Invalid material accepted',field,value))
    results.append({'independent_hex_base_and_frame_colours':True,'transparent_petg_preset_applied_to_frame':True,'invalid_materials_rejected':True})

    # Artist PNGs keep their full canvas. Back inputs are drawn as seen from the
    # back, without pre-mirroring; only their 3D placement reverses world X.
    dpi=cfg['print']['dpi'];size=(round(70/25.4*dpi),round(60/25.4*dpi))
    cap_px=round(14.64/25.4*dpi);cap=Image.new('RGBA',(cap_px,cap_px))
    ImageDraw.Draw(cap).rectangle((cap_px//4,cap_px//4,cap_px//3,cap_px//3),fill='#ff0000')
    cap_path=tmp/'cap-canvas.png';cap.save(cap_path)
    cap_cfg=copy.deepcopy(cfg);cap_cfg['print']['trim_transparent_padding']=False
    cap_key={**cap_cfg['keycaps'][0],'image':str(cap_path),'artwork_size_mm':[14.64,14.64],'rotation_deg':0}
    assert np.array_equal(np.asarray(artwork_canvas(cap_key,14.64,cap_cfg)),np.asarray(cap)),'Artist keycap canvas moved or resized'
    art=Image.new('RGBA',size);draw=ImageDraw.Draw(art)
    for colour,box in [('#ff0000',(.12,.12,.22,.25)),('#00ff00',(.72,.12,.82,.25)),('#0000ff',(.12,.72,.22,.85))]:
        draw.rectangle(tuple(round(v*size[i%2]) for i,v in enumerate(box)),fill=colour)
    for x,y in [(3.5,3.5),(66.5,3.5),(3.5,56.5),(66.5,56.5)]:
        draw.ellipse(((x-2)/70*size[0],(60-y-2)/60*size[1],(x+2)/70*size[0],(60-y+2)/60*size[1]),fill='#ff00ff')
    path=tmp/'board.png';art.save(path)
    board_cfg=copy.deepcopy(cfg)
    for side in ('front','back'):
        board_cfg['board'][side]={'image':str(path),'artwork_size_mm':[70,60],'centre_mm':[35,30],'rotation_deg':0}
        canvas=np.asarray(board_artwork_canvas(board_cfg,side))
        assert np.array_equal(canvas[round(size[1]*.18),round(size[0]*.17)],[255,0,0,255])
        assert np.array_equal(canvas[round(size[1]*.18),round(size[0]*.77)],[0,255,0,255])
        assert canvas[round((60-3.5)/60*size[1]),round(3.5/70*size[0]),3]==0,'Mounting hole must be clear'
        assert canvas[round((60-3.5)/60*size[1]),round(5.3/70*size[0]),3]>0,'Artwork outside mounting hole must remain'
    board_items=preview.scene(config=board_cfg)
    for side,view in [('front',(0,0,100)),('back',(0,0,-100))]:
        obj=next(o for o in board_items if o['name']=='board-artwork-'+side)
        output=tmp/f'{side}-orientation.png';preview.render([obj],output,view=view)
        rgb=np.asarray(Image.open(output))
        red=np.argwhere((rgb[:,:,0]>240)&(rgb[:,:,1]<10)&(rgb[:,:,2]<10))
        green=np.argwhere((rgb[:,:,1]>240)&(rgb[:,:,0]<10)&(rgb[:,:,2]<10))
        blue=np.argwhere((rgb[:,:,2]>240)&(rgb[:,:,0]<10)&(rgb[:,:,1]<10))
        assert len(red) and len(green) and len(blue)
        assert red[:,1].mean()<green[:,1].mean() and red[:,0].mean()<blue[:,0].mean(),side
    # Check the flat PCB previews too: Matplotlib reverses the back axis, so it
    # must compensate when placing the already face-oriented artist image.
    import render_board as pcb_preview
    with patch.object(pcb_preview,'CFG',board_cfg):
        for side in ('F','B'):
            fig,ax=pcb_preview.plt.subplots(figsize=(4,4));pcb_preview.render(ax,side)
            out=tmp/f'pcb-{side}.png';fig.savefig(out,dpi=100);pcb_preview.plt.close(fig)
            rgb=np.asarray(Image.open(out).convert('RGB'))
            red=np.argwhere((rgb[:,:,0]>240)&(rgb[:,:,1]<10)&(rgb[:,:,2]<10))
            green=np.argwhere((rgb[:,:,1]>240)&(rgb[:,:,0]<10)&(rgb[:,:,2]<10))
            blue=np.argwhere((rgb[:,:,2]>240)&(rgb[:,:,0]<10)&(rgb[:,:,1]<10))
            assert len(red) and len(green) and len(blue)
            assert red[:,1].mean()<green[:,1].mean() and red[:,0].mean()<blue[:,0].mean(),side
    with patch.object(appearance,'BUILD',tmp/'exports'):
        pack=appearance.export_print_pack(board_cfg,preview.FACES)
        for side in ('front','back'):
            entry=pack['board'][side];out=tmp/'exports/print-pack'/entry['artwork_png']
            assert entry['has_artwork'] and entry['mirrored'] is False
            with Image.open(out) as image:assert image.size==size
            svg=(out.with_suffix('.svg')).read_text();assert 'width="70mm"' in svg and 'height="60mm"' in svg
    missing={'image':str(tmp/'not-supplied.png'),'optional':True}
    assert resolve_image(missing) is None
    missing['fallback_image']='default-keycap.png'
    assert resolve_image(missing).name=='default-keycap.png'
    missing['optional']=False
    try:resolve_image(missing)
    except FileNotFoundError:pass
    else:raise AssertionError('Missing mandatory artwork accepted')
    results.append({'board_png_canvas_position_preserved':True,'front_and_back_readable_without_manual_mirroring':True,'board_artwork_pack_has_physical_dimensions':True,'optional_drop_in_artwork_and_keycap_fallback':True})

    for name in ('board-front-guides.png','board-back-guides.png','board-front-blank.png','board-back-blank.png'):
        with Image.open(DESIGN/'templates'/name) as image:
            assert image.size==size,(name,image.size,size)
            if 'guides' in name:assert image.getbbox() is not None
    for name in ('keycap-guides.png','keycap-blank.png'):
        with Image.open(DESIGN/'templates'/name) as image:assert image.size==(round(14.64/25.4*dpi),)*2
    results.append({'artist_guides_and_blank_canvases_match_export_dimensions':True})
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
canonical={'frame-cross-section.png',
           'top-frame-reinforced-assembly.png','top-frame-reinforced-without-keycaps.png',
           'top-frame-reinforced-top.png','top-frame-reinforced-print.png','top-frame-reinforced-exploded.png'}
assert canonical<=png_names
assert png_names == canonical, ('Superseded renders remain', png_names-canonical)
frame_report=json.loads((BUILD/'exports/top-frame-checks.json').read_text())
assert len(frame_report['frames'])==1 and frame_report['frames'][0]['file']=='top-frame-reinforced.stl'
assert frame_report['frames'][0]['link_width_mm']==2 and frame_report['frames'][0]['arm_width_mm']==2.4
assert len(frame_report['frames'][0]['measured_standoffs'])==4
assert all(abs(post['height_mm']-6)<.00002 for post in frame_report['frames'][0]['measured_standoffs'])
assert all(abs(post['wall_thickness_mm']-.8)<.00002 for post in frame_report['frames'][0]['measured_standoffs'])
sections=json.loads((BUILD/'exports/frame-section-dimensions.json').read_text())
assert len(sections)==1 and sections[0]['actual_screw_mm']==12
assert sections[0]['frame_foot_height_mm']==6 and sections[0]['opening_mm']==[14.0,14.75]
assert sections[0]['plate_thickness_mm']==1.0
assert sections[0]['head_recess_mm']==0 and sections[0]['nut_engagement_mm']==2.0
assert sections[0]['frame_foot_wall_mm']==.8 and sections[0]['frame_foot_diameter_mm']==5.0
for section in sections:
    positions=section['annotations']
    assert section['separate_washers']==0 and section['actual_screw_mm']==section['original_base_screw_mm']+6
    assert any('no washers' in x['label'] for x in positions)
    for a,b in zip(positions,positions[1:]):
        assert a['label_y']-b['label_y'] >= .26*(len(a['label'].split('\n'))+len(b['label'].split('\n')))+.35-1e-6
assert not (BUILD/'exports/top-frame.stl').exists(), 'Removed original frame export remains'
results.append({'vendor_pack_matches_configured_artwork':True,'identical_artwork_deduplicated':True,'reinforced_frame_views_present':True,'section_annotation_spacing':True})
(BUILD/'exports/appearance-checks.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'{len(results)} appearance, artwork, print-pack and annotation checks passed.')
