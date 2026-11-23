# Colours and printed keycap artwork

Edit **`case/appearance.json`**, then run from the **project root** (`macropad/`):

```bash
make preview
```

This regenerates the existing PNG views, updates `build/generated/appearance.scad` for OpenSCAD, and refreshes `build/print-pack/`. RGB values are integers from 0 to 255. Opacity is 0 to 1. Keep the six entries in SW1–SW6 order: SW1–SW3 are the row next to the OLED/USB, left to right when looking from the user side; SW4–SW6 are the front row.

```json
{
  "id": "SW1",
  "rgb": [30, 120, 220],
  "opacity": 1.0,
  "image": "artwork/ic-hack-logo.png",
  "artwork_size_mm": [12, 12],
  "rotation_deg": 0
}
```

Each key can use its own RGB, opacity, image path, size and rotation. Paths are relative to the case folder, or absolute. PNG, JPEG and WebP are supported; use a transparent PNG to show the keycap colour around the artwork. Set `"image": null` for a blank cap. Image aspect ratio is preserved. Transparent padding is cropped by default, and rotated images automatically shrink to fit inside the safe area. The top of the image points towards the USB edge; positive rotation is counterclockwise looking down at the key.

The initial artwork is one background-free IC Hack logo shared by all six keys. It was extracted from the user's local logo reference, with the pale backing and year removed. It is temporary print artwork; replace its path independently for any key when the final designs are ready.

`case.base` controls the base `rgb` and `opacity`. The optional minimal switch frame uses the same RGB, rendered opaque so its thin links stay visible. There is no separate frame material setting:

```json
"base": {"rgb": [55, 78, 97], "opacity": 0.45}
```

Use opacity 1 for opaque, around 0.45–0.7 for a see-through illustration, or 0 to hide that part in the rendered view. The preview blends surfaces and shows internal parts, with optional approximate haze. It does not model physical refraction or predict the light transmission and finish of a particular material. Colours also show in OpenSCAD. To sync CAD colours without rendering images, run `make prepare`. `build/generated/appearance.scad` is generated; edit the JSON instead. The cross-section uses solid material colours so its geometry remains legible.

With the planned FDM process, [clear PETG is a realistic choice for a translucent case](https://help.prusa3d.com/article/petg_2059). A [clear resin part with sanding/polishing or clear coating](https://formlabs.com/blog/3d-printing-transparent-parts-techniques-for-finishing-clear-resin/) is a better route to a glass-like transparent finish. Preview opacity is a design setting, not a promised printed finish.

## Supplier artwork pack

`build/print-pack/manifest.json` and `build/print-pack/keycaps.csv` map each cap to its RGB target and top-face artwork. Each unique design gets one transparent PNG and one dimensioned SVG wrapper; identical logo designs are shared rather than copied six times. The SVG embeds the raster artwork and is not a vector redraw of the logo. PNGs include DPI metadata (600 DPI by default). Increasing DPI does not create new detail in a low-resolution source image.

The current placeholder cap has a **14.64 × 14.64 mm flat top**. Artwork defaults to a centred **12 × 12 mm maximum frame**, preserving the image proportions, with at least 0.6 mm safe margin. The PNG/SVG print asset contains only artwork on transparency, not a painted rectangle of the cap body colour. Cap body colours are separate RGB targets in the manifest.

The supplier should confirm their actual 1u MX profile/template, printable region, bleed, colour proof, cap material and print process. These exports describe the design, not production tooling. The keycap meshes are visual references rather than a manufacturer's stem/profile model.

**OpenSCAD handles solid colours and opacity but does not display bitmap decals.** The Python renderer applies the images to the top faces, and the supplier pack carries the artwork. STL files contain geometry only; send the artwork pack alongside the specification rather than expecting colour or printed images in an STL.

## Verification

```bash
make check
```

Checks independent cap RGB assignment, centred placement, image orientation, transparent image padding, per-pixel opacity ordering/occlusion, supplier mappings, deduplication, and the cross-section label layout for both screw lengths.

## Current frame previews

`make preview` refreshes both washer-free frame versions, their assemblies, exploded views and the dimensioned cross-section. The compact base uses M3 × 10 mm screws; it is the only active screw setup. Both use the same colour/artwork settings. The old open-top assembly, separate-washer and PETG-study renders have been removed from the current preview set.

PCB silkscreen is extracted automatically by `make prepare`. Graphic positions follow the board; text uses an approximate font. `build/generated/pcb-silkscreen.png` is a presentation texture, not fabrication silkscreen. Add decorative artwork to the PCB's actual F.SilkS layer and then run `make preview`.

The screen reference still assumes 2.5 mm header housings, a full-width support shelf with header relief and a level case rim. See [TOP-FRAME.md](TOP-FRAME.md) for current views and installation details.
