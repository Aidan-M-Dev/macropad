# Appearance configuration

The editable configuration is now [`appearance/config.json`](../appearance/config.json), with image inputs in [`appearance/images/`](../appearance/images/) and PNG drawing guides in [`appearance/templates/`](../appearance/templates/).

See the [appearance handoff guide](../appearance/README.md) for the artist workflow, hex colours, translucent PETG, image filenames, key ordering and front/back orientation. No KiCad knowledge is required to make the artwork.

Run `make preview` to refresh all current assembly and PCB previews and the artwork pack. `make templates` regenerates the artist's guides. The previous RGB-array configuration in this directory has been replaced by the single handoff config.

The base, retaining frame and each keycap have independent colours and material presets. OpenSCAD uses the generated solid colours and opacity; bitmap artwork appears in the Python renders and the print pack. STL files remain geometry only.

`build/print-pack/manifest.json` and `keycaps.csv` include the selected hex colours, material and opacity. Keycap artwork is deduplicated into transparent PNGs and dimensioned SVG wrappers. `board-front.png` / `board-back.png` and their SVG wrappers are face-view artwork layers with USB at the top; the back is not pre-mirrored. These are artwork exports, not regenerated fabrication files.

The keycap profile, safe area and 14.64 mm top face remain provisional references. Confirm a supplier's actual printable region before production. The PCB's existing silkscreen is retained in the previews, with custom board artwork beneath it.
