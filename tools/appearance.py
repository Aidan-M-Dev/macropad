"""Shared RGB/opacity settings and transparent top-face artwork for CAD, previews and print."""
from pathlib import Path
import json,math,hashlib,base64,csv,io
import numpy as np
from PIL import Image,ImageOps
from paths import CASE as ROOT, BUILD, GENERATED

def load_config(path=None,require_images=True):
    path=Path(path) if path else ROOT/'appearance.json'
    if not path.is_absolute():path=ROOT/path
    cfg=json.loads(path.read_text())
    def material(m,label):
        rgb=m['rgb'];alpha=m.get('opacity',1)
        if not isinstance(rgb,list) or len(rgb)!=3 or not all(isinstance(x,int) and not isinstance(x,bool) and 0<=x<=255 for x in rgb):raise ValueError(f'{label}: rgb must be three integers 0..255')
        if not isinstance(alpha,(int,float)) or not 0<=alpha<=1:raise ValueError(f'{label}: opacity must be 0..1')
        for key,upper in [('frosted_blur_px',20),('layer_height_mm',2),('layer_line_strength',1)]:
            value=m.get(key,0)
            if not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=upper:raise ValueError(f'{label}: invalid {key}')
    for name in ['base']:material(cfg['case'][name],f'case.{name}')
    if len(cfg['keycaps'])!=6:raise ValueError('Exactly six keycap entries are required')
    for i,key in enumerate(cfg['keycaps']):
        if key.get('id')!=f'SW{i+1}':raise ValueError('Key entries must be in SW1..SW6 order')
        material(key,key['id'])
        if len(key['artwork_size_mm'])!=2 or any(not isinstance(v,(float,int)) or v<=0 for v in key['artwork_size_mm']):raise ValueError('Artwork dimensions must be positive')
        if not isinstance(key.get('rotation_deg',0),(int,float)) or not math.isfinite(key.get('rotation_deg',0)):raise ValueError('Artwork rotation must be a finite number')
        if key.get('image') and require_images:
            image_path=asset_path(key['image'])
            if not image_path.exists():raise FileNotFoundError(f'{key["id"]}: missing artwork {image_path}')
            with Image.open(image_path) as image:image.verify()
    if not 72<=cfg['print']['dpi']<=2400:raise ValueError('Print DPI must be 72..2400')
    if cfg['print']['safe_margin_mm']<0:raise ValueError('Safe margin cannot be negative')
    return cfg

def asset_path(path):
    path=Path(path)
    return path if path.is_absolute() else ROOT/path

def sync_scad(cfg):
    rows=['// Generated from case/appearance.json by tools/appearance.py. Edit the JSON, then rerender.',
          '// RGB channels are 0..255. Alpha is preview opacity, not a material specification.']
    for name in ['base']:
        rows += [f'appearance_case_{name}_rgb = {json.dumps(cfg["case"][name]["rgb"])};',f'appearance_case_{name}_opacity = {cfg["case"][name].get("opacity",1)};']
    rows += [f'appearance_keycap_rgbs = {json.dumps([k["rgb"] for k in cfg["keycaps"]])};',f'appearance_keycap_opacities = {json.dumps([k.get("opacity",1) for k in cfg["keycaps"]])};']
    GENERATED.mkdir(parents=True, exist_ok=True)
    out='\n'.join(rows)+'\n';path=GENERATED/'appearance.scad'
    if not path.exists() or path.read_text()!=out:path.write_text(out)

def artwork_canvas(key,face_mm,cfg):
    """Transparent, square top-face artwork; keep image aspect ratio and fit rotation safely."""
    dpi=cfg['print']['dpi'];px=round(face_mm/25.4*dpi)
    if px<1:raise ValueError('Invalid printable face')
    canvas=Image.new('RGBA',(px,px),(0,0,0,0))
    if not key.get('image'):return canvas
    with Image.open(asset_path(key['image'])) as source:art=ImageOps.exif_transpose(source).convert('RGBA')
    if cfg['print'].get('trim_transparent_padding',True):
        box=art.getchannel('A').getbbox()
        if box:art=art.crop(box)
    requested=[max(1,round(v/25.4*dpi)) for v in key['artwork_size_mm']]
    art=ImageOps.contain(art,tuple(requested),method=Image.Resampling.LANCZOS)
    angle=key.get('rotation_deg',0)%360
    if angle:art=art.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
    safe_mm=face_mm-2*cfg['print']['safe_margin_mm']
    if safe_mm<=0:raise ValueError('Safe margin consumes the entire top face')
    safe_px=max(1,round(safe_mm/25.4*dpi))
    art.thumbnail((safe_px,safe_px),Image.Resampling.LANCZOS)
    canvas.alpha_composite(art,((px-art.width)//2,(px-art.height)//2))
    return canvas

def export_print_pack(cfg,faces):
    """Deduplicate identical art; ship RGBA PNG + dimensioned SVG and per-key RGB manifest."""
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
        entries.append({'key':key['id'],'row':'USB row' if i<3 else 'user row','column':i%3+1,'body_rgb':key['rgb'],'preview_opacity':key.get('opacity',1),'source_image':key.get('image'),'artwork_png':filename,'artwork_svg':svgname,'top_face_mm':[mm,mm],'artwork_size_mm':key['artwork_size_mm'],'rotation_deg':key.get('rotation_deg',0),'png_pixels':list(art.size)})
    manifest={'units':'mm','face':'top','orientation':'Image top points towards USB edge; keys viewed from above with USB at top.','rgb_note':'sRGB design targets; supplier colour proof and material matching required.','production_note':'Preview keycap profile and print area are provisional. Confirm vendor cap profile, safe area/bleed, material and printing process before production. STL contains geometry only, not colour or printed artwork.','dpi':cfg['print']['dpi'],'safe_margin_mm':cfg['print']['safe_margin_mm'],'case':cfg['case'],'keys':entries,'generated_files':sorted(generated)}
    # Remove only obsolete files that this exporter previously owned.
    for name in old.get('generated_files',[]):
        if name not in generated and Path(name).name==name and name.startswith('artwork-'):(out/name).unlink(missing_ok=True)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with (out/'keycaps.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['key','row','column','R','G','B','artwork','top_face_width_mm','rotation_deg'])
        for e in entries:writer.writerow([e['key'],e['row'],e['column'],*e['body_rgb'],e['artwork_png'],e['top_face_mm'][0],e['rotation_deg']])
    return manifest

if __name__=='__main__':
    cfg=load_config(require_images=False);sync_scad(cfg);print('build/generated/appearance.scad updated from case/appearance.json')
