# Printable accessories

The retaining frame replaces all separate washers. The washer parts below are legacy accessories for using the base without a frame; they are not needed for the current frame assembly.

Run `make prepare` from the project root before opening these files in OpenSCAD.

| Source | Output after `make build` |
| --- | --- |
| [`washers-0.6mm.scad`](washers-0.6mm.scad) | `../build/exports/accessories/washers-0.6mm.stl` — four washers on the print bed |
| Shared `washer()` module | `../build/exports/accessories/washer-0.6mm.stl` — one washer |
| [`nut-fit-test-m3.scad`](nut-fit-test-m3.scad) | `../build/exports/accessories/nut-fit-test-m3.stl` — labelled M3 pocket coupon |
| [`keycap.stl`](keycap.stl) | `../build/exports/keycap.stl` — printable clicker keycap |

[`parts.scad`](parts.scad) contains the accessory modules. The entry points include the shared enclosure model, which supplies the dimensions and nut-pocket geometry. Change shared fastener dimensions in `../case/macropad_case.scad`; change accessory layouts in `parts.scad`.

Washers are 5 mm OD × 3.4 mm bore × 0.6 mm thick. Print four with the selected base. The nut tester has six pockets from 5.45 to 5.85 mm across flats; print it with the same settings and material as the enclosure. The raised number is pocket width, not screw diameter. Both enclosure variants now use **5.70 mm** pockets, enlarged after the final 5.60 mm case pockets were too tight despite the coupon fit.

`keycap.stl` is a copy of `keyboard-fidget-pin-retention/orange-keycap.stl` from the clicker project, at its original print scale. The local source copy keeps this project independent; `make build` restores its export after `make clean`.

Run `make check` after changes. See [printing, nut fit and assembly](../case/README.md) for the full instructions.
