# IC Hack macropad — base and retaining frame

The existing compact printed base with four M3 through-screws and four underside M3 nuts accepts the retaining frame. PCB: **70 × 60 × 1.6 mm**, mounting holes on **63 × 53 mm** spacing.

**Current retaining top:** the [reinforced switch frame](TOP-FRAME.md) attaches to those same four mounts, with keycaps above it and the OLED exposed. The only frame has 14.0 × 14.75 mm slots (left/right × top/bottom), 6 mm straight standoffs with 0.8 mm walls, a flat 1 mm plate, 2 mm links, 2.4 mm mounting arms and M3 × 12 mm screws. The top has no screw-head recesses. No separate washers are needed. Earlier base prints still fit the frame; reprint the updated base to get the smaller USB opening. The tall version has been retired. See the guide for installation and the new cross-section. The base-only washer stack below is retained as a reference for use without the frame.

| Base-only screws, without frame (under-head length) | Printable base | Overall case size | PCB-to-floor space |
| --- | --- | --- | --- |
| Four M3 × 6 mm — shortest reasonable even length | [base-m3x6.stl](../build/exports/base-m3x6.stl) | 72.3 × 62.3 × 8.0 mm | 3.8 mm |

All four walls and the screen shelf finish at the same height: **8.0 mm** overall, or **2.2 mm above the PCB**. A **3.8 mm roof** closes the top of the reduced USB opening, level with the rear rim.

For the base-only setup without a frame, print one base and [four washers together](../build/exports/accessories/washers-0.6mm.stl), or print four copies of [the single washer](../build/exports/accessories/washer-0.6mm.stl). Washers are **5 mm OD × 3.4 mm bore × 0.6 mm tall**. All printable meshes lie on Z=0; no hardware or electronic reference meshes belong on the print plate.

## Prototype changes

The USB-C body is modelled **entirely beneath the PCB**, **9.8 mm wide × 3.5 mm tall below its underside**. “3.5 mm deep” is interpreted as its vertical projection below the board. Its XY position still comes from J1. The port is **10.4 mm wide × 3.8 mm high**, with **0.3 mm clearance below the connector**. The top has been lowered by **exactly 3 mm**, from Z=7.2 to Z=4.2; the bottom remains at Z=0.4. The new upper edge is flat, retaining the old lower rounded corners. This preserves the full connector width at the ceiling, with **zero nominal clearance above the modelled connector**. The roof is now **3.8 mm thick**, finishing at the unchanged rim. `usb_top_reduction=3` sets the crop, added to the original `usb_bridge_layers=4` roof at 0.2 mm layers. The USB body remains a fit reference; check the actual plug fit because cable-overmould dimensions were not supplied.

The required bottom component envelope is now **3.5 mm** from the PCB underside. The compact version provides **3.8 mm above the inside floor**, with the extra 0.3 mm coming from the base-only screw/nut stack. The flat-top frame assembly gives **2.0 mm nut engagement** with M3 × 12 mm screws; screw tips are **0.8 mm above the exterior underside** and nut bottoms remain **0.4 mm above it**. Without the frame, M3 × 6 mm screws give full 2.4 mm engagement and 0.4 mm tip recess.

Nut pockets are **5.70 mm across flats**, enlarged after the final 5.60 mm case pockets were too tight despite the coupon fit. With nominal 5.5 mm M3 nuts this gives **0.20 mm total clearance**, plus the existing 0.25 mm entry lead-in on each side. This fit is retained in the selected compact base. `nut_fit_allowance` is total across-flats allowance, not per side.

The compact M3 × 6 stack uses a **1.4 mm sloped roof above the nut seat**, retaining a **0.25 mm bearing ledge** and at least two extrusion lines around the pocket. The integral support finishes at the PCB underside. The next shorter even screw, M3 × 4, cannot satisfy the 3.5 mm bottom clearance and the required nut roof. Case height excludes electronics and screw heads.

## Screen support shelf

A rear-wall ledge spans the **full 38 mm width of the OLED**, ending at the screen's edges. Local relief leaves **0.5 mm clearance** around the OLED header housings for tilted insertion, and the rear screws remain accessible. Its underside rises at **30° above the print bed**, extending the shelf **about 1.88 mm beneath the OLED footprint**, with a **0.25 mm entry chamfer**. `screen_shelf_overlap` sets the minimum overlap; the selected slope can extend it further. The shelf target is **2.25 mm above the main PCB**. It rounds **down** to whole print layers, giving **2.2 mm at the default 0.2 mm layers** and leaving **0.3 mm below the assumed 2.5 mm header housings**. It limits screen flex rather than preloading the solder joints.

All walls rise to the shelf's height, giving a level rim. The shelf root blends into the rear wall. Its sloped underside leaves the PCB clear; there is no post through the PCB. To install a board with the screen already soldered on, offer the rear/USB edge under the shelf with the front tilted up, guide the USB connector into its opening, then lower the front onto the screw supports. The entry chamfer helps the screen pass over the ledge. Exact CSG checks cover the PCB, screen and USB connector at 2°, 4° and 6° front-up insertion angles; these are geometry checks of the assumed component envelopes, not a physical fit result.

## M3 nut grip tester

Print [nut-fit-test-m3.stl](../build/exports/accessories/nut-fit-test-m3.stl) flat, with its raised labels facing up, using the **same material, line width, layers and hole-compensation settings as the case**. The coupon is **66 × 16 × 4.2 mm** and has six labelled hex pockets: **5.45, 5.50, 5.60, 5.70, 5.80 and 5.85 mm across flats**. All are for the same nominal M3 nut; the labels give **pocket width**, not screw diameter. The case now uses **5.70 mm** pockets; 5.60 mm fitted the coupon but was too tight in the final case. 5.45 mm reproduces the older tight pocket.

Turn the coupon over to insert a nut from underneath. Use the same actual M3 nut to compare each pocket, seating it against the roof. Choose the smallest pocket that seats without excessive force and holds the nut securely. The coupon uses the case's actual shared nut-pocket geometry: **0.8 mm walls, 0.25 mm entry lead-in, 2.4 mm nut thickness, 0.4 mm nut inset, 1.4 mm tapered roof and 3.4 mm screw bore**. Each pocket is separate but joined to the same thin base strip.

To apply your chosen size, set `nut_fit_allowance = chosen_pocket_af - nut_af` in `macropad_case.scad` and rebuild. For example, 5.80 mm with a nominal 5.50 mm nut means `nut_fit_allowance=0.30`. The largest coupon size fits the compact case's existing roof taper; check the parameter assertions before increasing beyond it.

[Tester source](../accessories/nut-fit-test-m3.scad)

All four insulating washers are identical **M3 clearance washers**: **3.4 mm bore, 5 mm OD, 0.6 mm thick**. Viewing angle and shading can make their apparent sizes differ. These are used only in the base-only setup; omit them with the retaining frame.

## Base-only printing and assembly (without retaining frame)

Use **0.4 mm extrusion width, 0.2 mm layers, two walls and two bottom layers**. The wall is **0.8 mm**, the flat bottom skin **0.4 mm**, and each washer is **three layers**. The underside retains its 0.6 mm round-over and broader 4 mm corners, blending into the upper outline over 2.4 mm. There are no ribs. The PCB has 0.35 mm clearance on each side; the protective rim rises **2.2 mm above it on all sides**, level with the screen shelf. The fully pressed reference keycaps remain **0.3 mm above the rim**.

1. Print one selected base and four 0.6 mm washers.
2. Insert four M3 nuts from underneath and seat them against their pocket roofs.
3. With the screen already soldered on, slide the rear/USB edge beneath the screen shelf, keeping the front tilted up. Guide the USB connector into its opening, then lower the PCB onto the integral supports.
4. Put a washer above each mounting hole and install four screws matching the base filename.
5. Tighten gently, then check the USB cable and key travel.

Hardware assumptions: regular M3 nuts **5.5 mm AF × 2.4 mm thick**; socket-cap screw heads **5.5 mm diameter × 3 mm tall**, with **2.5 mm Allen sockets**. Washer thickness is part of the screw stack: use 0.6 mm washers with these bases. Mechanical strength and the final printed nut grip need a physical fit check.

## Source and renders

- [base-m3x6.scad](base-m3x6.scad): existing compact printable-base entry point; use M3 × 12 mm with the reinforced frame.
- [../accessories/](../accessories/README.md): washer and nut-fit tester entry points and shared accessory modules.
- [macropad_case.scad](macropad_case.scad): shared parameterised model. `screw_length=6` retains the original compact-base datum; `with_top_frame=true` uses M3 × 12 mm for the reinforced frame; `part` selects assembly, exploded, section, print, base, washer, washer_set or nut_fit_test. OpenSCAD presets are in `macropad_case.json`.

[Reinforced frame views and cross-section](TOP-FRAME.md).

Colours, keycap artwork and opacity remain controlled by `../appearance/config.json`; see [APPEARANCE.md](APPEARANCE.md). PCB silkscreen is extracted from the existing KiCad board; these renders are visual references, not fabrication output. Keycaps and electronics are simplified references.

## Regeneration and verification

Run from the **project root** (`macropad/`):

```bash
make prepare   # Before opening the model directly in OpenSCAD
make build     # Printable parts, reference meshes and clearance checks
make preview   # Builds as needed, then regenerates all renders and artwork
make check     # Refreshes previews and runs the full checks
```

The Makefile handles dependencies, including extracting the PCB geometry when the KiCad board changes. Colour/artwork edits reuse meshes. Generated CAD inputs are in `../build/generated/`; edit the board or `../appearance/config.json` instead. Generated STLs, reports and logs are in `../build/exports/`, images in `../build/previews/`, and supplier artwork in `../build/print-pack/`.

`make build` checks empty CSG intersections, excluding intentional bearing-face contact, for the PCB, washers, screen (including its header housings), screen/PCB insertion, key travel, underside USB, the 3.5 mm component envelope, fasteners and hardware against electronics. `make check` also validates parameter assertions, measured STL sections, manifold geometry, artwork and annotation layout.

Run `make top-frame` to rebuild the reinforced frame, their current assembly renders and the dimensioned cross-section. Superseded base-only renders have been removed. See the [root guide](../README.md) for setup and the full folder layout.
