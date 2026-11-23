"""Hex colours, material presets and face-aligned artwork for CAD, previews and print."""
from pathlib import Path
import json,math,hashlib,base64,csv,io,re,copy
import numpy as np
from PIL import Image,ImageOps,ImageDraw,ImageChops
from paths import DESIGN, BUILD, GENERATED

def load_config(path=None,require_images=True):
    path=Path(path) if path else DESIGN/'config.json'
    if not path.is_absolute():path=DESIGN/path
    cfg=json.loads(path.read_text())
    def material(m,label):
        if 'colour' in m:
            colour=m['colour']
            if not isinstance(colour,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',colour):raise ValueError(f'{label}: colour must be #RRGGBB')
            m['rgb']=[int(colour[i:i+2],16) for i in (1,3,5)]
        rgb=m.get('rgb');kind=m.get('material','solid')
        if kind not in ('solid','transparent_petg'):raise ValueError(f'{label}: material must be solid or transparent_petg')
        m['material']=kind
        if kind=='transparent_petg':
            for key,value in {'opacity':.58,'frosted_blur_px':4,'layer_height_mm':.2,'layer_line_strength':.09}.items():m.setdefault(key,value)
        alpha=m.setdefault('opacity',1)
        if not isinstance(rgb,list) or len(rgb)!=3 or not all(isinstance(x,int) and not isinstance(x,bool) and 0<=x<=255 for x in rgb):raise ValueError(f'{label}: rgb must be three integers 0..255')
        if isinstance(alpha,bool) or not isinstance(alpha,(int,float)) or not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError(f'{label}: opacity must be 0..1')
        for key,upper in [('frosted_blur_px',20),('layer_height_mm',2),('layer_line_strength',1)]:
            value=m.get(key,0)
            if not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=upper:raise ValueError(f'{label}: invalid {key}')
        m.setdefault('colour','#'+''.join(f'{v:02X}' for v in rgb))
    cfg['case'].setdefault('frame',copy.deepcopy(cfg['case']['base']))
    for name in ['base','frame']:material(cfg['case'][name],f'case.{name}')
    material(cfg['board'],'board')
    def artwork(settings,label,position=False):
        size=settings['artwork_size_mm']
        if not isinstance(size,list) or len(size)!=2 or any(isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or v<=0 for v in size):raise ValueError(f'{label}: artwork dimensions must be positive')
        angle=settings.get('rotation_deg',0)
        if isinstance(angle,bool) or not isinstance(angle,(int,float)) or not math.isfinite(angle):raise ValueError(f'{label}: artwork rotation must be a finite number')
        if position:
            centre=settings['centre_mm']
            if not isinstance(centre,list) or len(centre)!=2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in centre):raise ValueError(f'{label}: centre_mm must be two finite numbers')
        if not isinstance(settings.get('optional',False),bool):raise ValueError(f'{label}: optional must be true or false')
        for key in ('image','fallback_image'):
            if settings.get(key) is not None and (not isinstance(settings[key],str) or not settings[key].strip()):raise ValueError(f'{label}: {key} must be a filename or null')
        if require_images:
            image_path=resolve_image(settings)
            if image_path:
                with Image.open(image_path) as image:image.verify()
    if len(cfg['keycaps'])!=6:raise ValueError('Exactly six keycap entries are required')
    for i,key in enumerate(cfg['keycaps']):
        if key.get('id')!=f'SW{i+1}':raise ValueError('Key entries must be in SW1..SW6 order')
        material(key,key['id'])
        artwork(key,key['id'])
    for side in ('front','back'):artwork(cfg['board'][side],f'board.{side}',position=True)
    if isinstance(cfg['print']['dpi'],bool) or not isinstance(cfg['print']['dpi'],int) or not 72<=cfg['print']['dpi']<=2400:raise ValueError('Print DPI must be an integer 72..2400')
    margin=cfg['print']['safe_margin_mm']
    if isinstance(margin,bool) or not isinstance(margin,(float,int)) or not math.isfinite(margin) or margin<0:raise ValueError('Safe margin must be a non-negative finite number')
    return cfg

def asset_path(path):
    path=Path(path)
    return path if path.is_absolute() else DESIGN/'images'/path

def resolve_image(settings):
    if not settings.get('image'):return None
    path=asset_path(settings['image'])
    if path.is_file():return path
    if not settings.get('optional',False):raise FileNotFoundError(f'Missing artwork: {path}')
    if settings.get('fallback_image'):
        fallback=asset_path(settings['fallback_image'])
        if not fallback.is_file():raise FileNotFoundError(f'Missing fallback artwork: {fallback}')
        return fallback
    return None

def sync_scad(cfg):
    rows=['// Generated from appearance/config.json by tools/appearance.py. Edit the JSON, then rerender.',
          '// RGB channels are 0..255. Alpha is preview opacity, not a material specification.']
    for name in ['base','frame']:
        rows += [f'appearance_case_{name}_rgb = {json.dumps(cfg["case"][name]["rgb"])};',f'appearance_case_{name}_opacity = {cfg["case"][name].get("opacity",1)};']
    rows += [f'appearance_keycap_rgbs = {json.dumps([k["rgb"] for k in cfg["keycaps"]])};',f'appearance_keycap_opacities = {json.dumps([k.get("opacity",1) for k in cfg["keycaps"]])};']
    rows += [f'appearance_board_rgb = {json.dumps(cfg["board"]["rgb"])};']
    GENERATED.mkdir(parents=True, exist_ok=True)
    out='\n'.join(rows)+'\n';path=GENERATED/'appearance.scad'
    if not path.exists() or path.read_text()!=out:path.write_text(out)

def artwork_canvas(key,face_mm,cfg):
    """Keep the artist's canvas aligned; clip ink to the keycap's safe print area."""
    dpi=cfg['print']['dpi'];px=round(face_mm/25.4*dpi)
    if px<1:raise ValueError('Invalid printable face')
    canvas=Image.new('RGBA',(px,px),(0,0,0,0))
    source_path=resolve_image(key)
    if not source_path:return canvas
    with Image.open(source_path) as source:art=ImageOps.exif_transpose(source).convert('RGBA')
    if cfg['print'].get('trim_transparent_padding',True):
        box=art.getchannel('A').getbbox()
        if box:art=art.crop(box)
    requested=[max(1,round(v/25.4*dpi)) for v in key['artwork_size_mm']]
    art=ImageOps.contain(art,tuple(requested),method=Image.Resampling.LANCZOS)
    angle=key.get('rotation_deg',0)%360
    if angle:art=art.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
    safe_mm=face_mm-2*cfg['print']['safe_margin_mm']
    if safe_mm<=0:raise ValueError('Safe margin consumes the entire top face')
    canvas.alpha_composite(art,((px-art.width)//2,(px-art.height)//2))
    margin=round(cfg['print']['safe_margin_mm']/25.4*dpi)
    mask=Image.new('L',canvas.size);ImageDraw.Draw(mask).rectangle((margin,margin,px-margin-1,px-margin-1),fill=255)
    canvas.putalpha(ImageChops.multiply(canvas.getchannel('A'),mask))
    return canvas

def board_artwork_canvas(cfg,side):
    """Face-view artwork: left/right are as seen from that face, USB edge at top."""
    data=json.loads((GENERATED/'pcb_geometry.json').read_text())
    w,h=data['pcb_size'];scale=cfg['print']['dpi']/25.4
    size=(round(w*scale),round(h*scale));canvas=Image.new('RGBA',size)
    settings=cfg['board'][side];path=resolve_image(settings)
    if path:
        with Image.open(path) as source:art=ImageOps.exif_transpose(source).convert('RGBA')
        target=tuple(max(1,round(v*scale)) for v in settings['artwork_size_mm'])
        art=ImageOps.contain(art,target,Image.Resampling.LANCZOS)
        if settings.get('rotation_deg',0):art=art.rotate(settings['rotation_deg'],expand=True,resample=Image.Resampling.BICUBIC)
        cx,cy=settings['centre_mm']
        canvas.alpha_composite(art,(round(cx/w*size[0]-art.width/2),round((h-cy)/h*size[1]-art.height/2)))
    mask=Image.new('L',size);draw=ImageDraw.Draw(mask)
    draw.rounded_rectangle((0,0,size[0]-1,size[1]-1),radius=scale,fill=255)
    def face_x(x):return x if side=='front' else w-x
    for x,y in data['mount_holes']:
        x=face_x(x);r=1.6
        draw.ellipse(((x-r)*scale,(h-y-r)*scale,(x+r)*scale,(h-y+r)*scale),fill=0)
    x=face_x(data['usb_centre'][0]);draw.rectangle(((x-4.57)*scale,0,(x+4.57)*scale,4.51*scale),fill=0)
    canvas.putalpha(ImageChops.multiply(canvas.getchannel('A'),mask))
    return canvas

def export_print_pack(cfg,faces):
    """Export keycap and board PNG/SVG layers with colours, materials and placement metadata."""
    out=BUILD/'print-pack';out.mkdir(parents=True,exist_ok=True)
    old=json.loads((out/'manifest.json').read_text()) if (out/'manifest.json').exists() else {}
    generated=set();unique={};entries=[]
    for i,key in enumerate(cfg['keycaps']):
        mm=faces[i]['width_mm'];art=artwork_canvas(key,mm,cfg)
        signature=hashlib.sha256(art.tobytes()+str(mm).encode()).hexdigest()[:12]
        if signature not in unique:
            stem=f'artwork-{signature}';filename=stem+'.png';svgname=stem+'.svg'
            art.save(out/filename,dpi=(cfg['print']['dpi'],cfg['print']['dpi']))
            payload=io.BytesIO();art.save(payload,format='PNG');embedded=base64.b64encode(payload.getvalue()).decode()
            (out/svgname).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{mm:g}mm" height="{mm:g}mm" viewBox="0 0 {mm:g} {mm:g}"><image width="{mm:g}" height="{mm:g}" href="data:image/png;base64,{embedded}"/></svg>\n')
            unique[signature]=(filename,svgname)
            generated.update([filename,svgname])
        filename,svgname=unique[signature]
        resolved=resolve_image(key)
        entries.append({'key':key['id'],'row':'USB row' if i<3 else 'user row','column':i%3+1,'body_rgb':key['rgb'],'body_colour':key['colour'],'material':key['material'],'preview_opacity':key.get('opacity',1),'source_image':key.get('image'),'resolved_image':resolved.name if resolved else None,'artwork_png':filename,'artwork_svg':svgname,'top_face_mm':[mm,mm],'artwork_size_mm':key['artwork_size_mm'],'rotation_deg':key.get('rotation_deg',0),'png_pixels':list(art.size)})
    board={}
    for side in ('front','back'):
        art=board_artwork_canvas(cfg,side);png=f'board-{side}.png';svg=f'board-{side}.svg'
        art.save(out/png,dpi=(cfg['print']['dpi'],cfg['print']['dpi']))
        payload=io.BytesIO();art.save(payload,format='PNG');embedded=base64.b64encode(payload.getvalue()).decode()
        (out/svg).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="70mm" height="60mm" viewBox="0 0 70 60"><image width="70" height="60" href="data:image/png;base64,{embedded}"/></svg>\n')
        generated.update([png,svg]);resolved=resolve_image(cfg['board'][side])
        board[side]={'source_image':cfg['board'][side].get('image'),'resolved_image':resolved.name if resolved else None,'artwork_png':png,'artwork_svg':svg,'size_mm':[70,60],'mirrored':False,'view':'Looking at this face, USB edge at top','has_artwork':bool(art.getbbox())}
    manifest={'units':'mm','face':'top','orientation':'Image top points towards USB edge; keys viewed from above with USB at top.','rgb_note':'sRGB design targets; supplier colour proof and material matching required.','production_note':'Preview keycap profile and print area are provisional. Confirm vendor cap profile, safe area/bleed, material and printing process before production. STL contains geometry only, not colour or printed artwork. PCB layers are artwork exports; transfer approved art into the PCB fabrication design separately.','dpi':cfg['print']['dpi'],'safe_margin_mm':cfg['print']['safe_margin_mm'],'case':cfg['case'],'keys':entries,'board':board,'generated_files':sorted(generated)}
    # Remove only obsolete files that this exporter previously owned.
    for name in old.get('generated_files',[]):
        if name not in generated and Path(name).name==name and name.startswith('artwork-'):(out/name).unlink(missing_ok=True)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with (out/'keycaps.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['key','row','column','R','G','B','artwork','top_face_width_mm','rotation_deg','hex_colour','material','preview_opacity'])
        for e in entries:writer.writerow([e['key'],e['row'],e['column'],*e['body_rgb'],e['artwork_png'],e['top_face_mm'][0],e['rotation_deg'],e['body_colour'],e['material'],e['preview_opacity']])
    return manifest

if __name__=='__main__':
    cfg=load_config();sync_scad(cfg);print('Appearance config and image inputs validated; generated CAD colours updated.')
