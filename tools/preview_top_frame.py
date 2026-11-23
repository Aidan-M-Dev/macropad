"""Current M3x10 assembly, exploded and print views for both frame versions."""
from paths import BUILD
from preview import CFG, item, load, render, scene,finish

frame = CFG['case']['frame'];rgb = frame['rgb']


def frame_scene(reinforced=False, exploded=False, config=None):
    cfg=config or CFG
    frame=cfg['case']['frame'];rgb=frame['rgb']
    variant = 'frame-reinforced' if reinforced else 'frame'
    refs = BUILD/f'previews/meshes/{variant}-base6'
    data = [obj for obj in scene(length=6,config=cfg) if obj['name'] not in ('washers','top_screws','socket-interior')]
    data += [item('top-frame',load(refs/'top_frame_assembled.stl'),rgb,frame['opacity'],**finish(frame)),
             item('top_screws',load(refs/'top_screws.stl'),[184,190,198])]
    if exploded:
        # Match the OpenSCAD exploded preset: PCB/screen, frame, switches,
        # keycaps and screws are distinct layers; nuts sit below the base.
        for obj in data:
            name = obj['name']
            shift = (0 if name=='base' else -14 if name=='nuts' else
                     23.8 if name=='top-frame' else 35 if name=='switches' else
                     49 if name.startswith('keycap-') or name=='artwork' else
                     56 if name=='top_screws' else 14)
            obj['mesh'][:,:,2] += shift
        def bounds(name):
            meshes=[o['mesh'] for o in data if o['name']==name]
            return min(m[:,:,2].min() for m in meshes),max(m[:,:,2].max() for m in meshes)
        assert bounds('nuts')[1]<bounds('base')[0]
        assert bounds('pcb')[1]<bounds('top-frame')[0]
        assert bounds('top-frame')[1]<bounds('switches')[0]
        assert bounds('switches')[1]<bounds('keycap-1')[0]
        assert bounds('top-frame')[1]<bounds('top_screws')[0]
    return data


if __name__=='__main__':
    for reinforced in (False,True):
        prefix='top-frame-reinforced' if reinforced else 'top-frame'
        data=frame_scene(reinforced)
        render(data,f'{prefix}-assembly.png')
        exposed=[obj for obj in data if not obj['name'].startswith('keycap-') and obj['name']!='artwork']
        render(exposed,f'{prefix}-without-keycaps.png',view=(55,-80,170))
        render(exposed,f'{prefix}-top.png',view=(0,0,150))
        render(frame_scene(reinforced,exploded=True),f'{prefix}-exploded.png',view=(80,-110,75))
        render([item('top-frame',load(BUILD/f'exports/{prefix}.stl'),rgb,frame['opacity'],**finish(frame))],f'{prefix}-print.png')

    from PIL import Image, ImageDraw, ImageFont
    images = [Image.open(BUILD/f'previews/{name}').convert('RGB').resize((800,600))
              for name in ('top-frame-print.png','top-frame-reinforced-print.png')]
    comparison = Image.new('RGB',(1600,660),(18,25,35))
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24)
    draw = ImageDraw.Draw(comparison)
    for i,(image,label) in enumerate(zip(images,('Minimal: 1.2 mm links / 1.6 mm arms','Reinforced: 2.0 mm links / 2.4 mm arms'))):
        comparison.paste(image,(800*i,60))
        draw.text((800*i+24,20),label,font=font,fill=(235,239,242))
    comparison.save(BUILD/'previews/top-frame-comparison.png')
