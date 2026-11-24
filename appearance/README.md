# Appearance handoff

You only need an image editor and this folder. No KiCad or CAD editing is required.

## Make the images

1. Open a **blank** PNG from [`templates/`](templates/).
2. Import its matching **guides** PNG as a separate layer above it. Keep both layers aligned at the top-left; do not resize the canvas.
3. Draw on your own layers. The board guides show the real PCB edge, holes, pads, traces, component outlines and a 5 mm grid. Keep important artwork clear of components, holes and contacts. Front and back are each shown **looking at that face with USB at the top**; do not mirror the back artwork yourself.
4. Hide the guide layer before exporting. Save a transparent PNG into [`images/`](images/) using one of the names below. Keep your layered editor files separately.

| Design | Blank canvas | Guide layer | Save in `images/` as |
| --- | --- | --- | --- |
| PCB front | [board-front-blank.png](templates/board-front-blank.png) | [board-front-guides.png](templates/board-front-guides.png) | `board-front.png` |
| PCB back | [board-back-blank.png](templates/board-back-blank.png) | [board-back-guides.png](templates/board-back-guides.png) | `board-back.png` |
| Any keycap | [keycap-blank.png](templates/keycap-blank.png) | [keycap-guides.png](templates/keycap-guides.png) | `SW1.png` through `SW6.png` |

At the default 600 DPI, board canvases are **1654 × 1417 pixels** (70 × 60 mm); keycap canvases are **346 × 346 pixels** (14.64 mm square). The orange rectangle on the keycap guide marks a **0.6 mm safe margin**: artwork outside it is clipped. Blue marks the top-face boundary; grey lines mark the centre. The top of every keycap image points towards USB.

Key names, looking down at the macropad:

```text
       USB / OLED
     SW1  SW2  SW3
     SW4  SW5  SW6
```

You can supply any subset of the eight images. Missing `SW1.png`–`SW6.png` use [`default-keycap.png`](images/default-keycap.png); missing board files leave that face undecorated. Replacing `default-keycap.png` changes all keys that have no individual image. Set an entry's `image` to `null` in the config for a completely blank key or board face.

## Choose colours and plastic

Edit [`config.json`](config.json). Colours are **six-digit hex codes**, with the `#` included. `case.base` and `case.frame` are independent, and every keycap has its own colour.

```json
"base": {"colour": "#374E61", "material": "solid"},
"frame": {"colour": "#D7E1E4", "material": "transparent_petg"}
```

Use `solid` for opaque plastic. `transparent_petg` gives a frosted translucent preview with opacity 0.58 and visible print layers. Use a pale colour such as `#D7E1E4` for natural clear PETG, or a tint for coloured translucent PETG. You may add `"opacity": 0.7` to override the preview opacity (0 invisible, 1 opaque). This is a visual approximation of printed PETG, not a prediction of the physical finish.

For the normal template workflow, leave image sizes, centres and rotations as supplied. If needed, `artwork_size_mm` sets the maximum image dimensions, `rotation_deg` rotates counterclockwise, and board `centre_mm` is measured from the bottom-left **as seen from that face**. Aspect ratio is preserved. Transparent padding is kept so artwork stays aligned with the guides.

## Send it back

Return this whole folder, including `config.json` and the images. The developer runs **`make preview`** from the repository root to apply the colours and artwork to the reinforced frame, refresh the PCB front/back preview, and export artwork into `build/print-pack/`. `make templates` regenerates the guides if the PCB layout changes.

The developer can run `python3 tools/package_appearance.py` to bundle this folder into `build/appearance-handoff.zip` for sharing.

The templates are drawing guides, not files to print on the board. Keep their lines out of the final images. Approved PCB graphics will be transferred into the fabrication design separately; this workflow does not change copper, solder mask or existing KiCad silkscreen.
