"""Package the image-editor handoff without requiring CAD tools on the artist's machine."""
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image

from appearance import load_config
from paths import BUILD, DESIGN

cfg = load_config()
dpi = cfg['print']['dpi']
for name in ('board-front', 'board-back', 'keycap'):
    expected = ((round(14.64/25.4*dpi),)*2 if name == 'keycap'
                else (round(70/25.4*dpi), round(60/25.4*dpi)))
    for kind in ('guides', 'blank'):
        path = DESIGN/'templates'/f'{name}-{kind}.png'
        with Image.open(path) as image:
            if image.size != expected:
                raise ValueError(f'{path.name}: regenerate with make templates before packaging')

BUILD.mkdir(parents=True, exist_ok=True)
out = BUILD/'appearance-handoff.zip'
files = sorted(p for p in DESIGN.rglob('*') if p.is_file()
               and not any(part.startswith('.') for part in p.relative_to(DESIGN).parts))
with ZipFile(out, 'w', ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, path.relative_to(DESIGN.parent))
with ZipFile(out) as archive:
    assert archive.testzip() is None
print(f'Packaged {len(files)} files in {out.name}.')
