# Run from the project root. GNU Make 4.3+ is required for grouped outputs (&:).
.DEFAULT_GOAL := help
.DELETE_ON_ERROR:

PYTHON ?= python3
export PYTHONDONTWRITEBYTECODE := 1

PCB := hardware/IC\ Hack\ Macro\ Pad.kicad_pcb
PCB_DATA := build/generated/pcb_geometry.scad build/generated/pcb_geometry.json build/generated/pcb_silkscreen.json
APPEARANCE := build/generated/appearance.scad
DESIGN_INPUTS := appearance/config.json $(wildcard appearance/images/*)
LENGTHS := 6
REFERENCE_PARTS := washers pcb switches keycaps screen_board screen_glass screen_face screen_contacts screen_components screen_headers usb top_screws nuts
PRINTABLES := $(foreach length,$(LENGTHS),build/exports/base-m3x$(length).stl) \
              build/exports/accessories/washer-0.6mm.stl build/exports/accessories/washers-0.6mm.stl build/exports/accessories/nut-fit-test-m3.stl
REFERENCES := $(foreach length,$(LENGTHS),$(addprefix build/previews/meshes/m3x$(length)/,$(addsuffix .stl,$(REFERENCE_PARTS))))
BASE_LOGS := $(foreach length,$(LENGTHS),build/exports/logs/m3x$(length)-base-m3x$(length).log)
MESH_OUTPUTS := $(PRINTABLES) $(REFERENCES) $(BASE_LOGS) build/exports/clearance-checks.json
FRAME_OUTPUTS := build/exports/top-frame-reinforced.stl build/exports/top-frame-checks.json \
                 $(foreach length,$(LENGTHS),$(addprefix build/previews/meshes/frame-reinforced-base$(length)/,$(addsuffix .stl,top_frame_assembled top_screws)))

.PHONY: help prepare build preview check board all clean top-frame templates

help:
	@echo "make prepare  Generate board datums and CAD colours (before opening OpenSCAD)"
	@echo "make build    Export printable parts, reference meshes and clearance checks"
	@echo "make preview  Build as needed, then refresh renders and keycap artwork pack"
	@echo "make check    Refresh previews and run all existing design checks"
	@echo "make board    Render front/back PCB images"
	@echo "make templates  Refresh the artist's PNG guides and blank canvases"
	@echo "make top-frame  Export and preview the reinforced switch retaining frame"
	@echo "make all      Run all checks and render the PCB"
	@echo "make clean    Remove generated build/ output"

prepare: $(PCB_DATA) $(APPEARANCE)

$(PCB_DATA) &: $(PCB) tools/extract_pcb.py tools/paths.py
	$(PYTHON) tools/extract_pcb.py

$(APPEARANCE): appearance/config.json tools/appearance.py tools/paths.py
	$(PYTHON) tools/appearance.py
	@touch $@

# One exporter owns this group. Missing outputs or changed geometry rebuild it.
# Colours are an order-only dependency: appearance edits do not change STL geometry.
$(MESH_OUTPUTS) &: $(wildcard case/*.scad accessories/*.scad) build/generated/pcb_geometry.scad tools/build.py tools/paths.py Makefile | $(APPEARANCE)
	$(PYTHON) tools/build.py

$(FRAME_OUTPUTS) &: case/macropad_case.scad case/top_frame_modules.scad tools/build_top_frame.py tools/preview.py $(MESH_OUTPUTS)
	$(PYTHON) tools/build_top_frame.py

build: prepare $(MESH_OUTPUTS) $(FRAME_OUTPUTS) build/exports/keycap.stl

top-frame: build
	$(PYTHON) tools/preview_top_frame.py
	$(PYTHON) tools/frame_section.py

build/exports/keycap.stl: accessories/keycap.stl
	mkdir -p $(@D)
	cp $< $@

preview: build
	$(PYTHON) tools/preview.py --assets-only
	$(PYTHON) tools/preview_top_frame.py
	$(PYTHON) tools/frame_section.py
	$(PYTHON) tools/render_board.py
	$(PYTHON) tools/package_appearance.py

check: preview
	$(PYTHON) tools/check_parameters.py
	$(PYTHON) tools/check_print_geometry.py
	$(PYTHON) tools/check_appearance.py

templates: prepare
	$(PYTHON) tools/render_board.py --templates-only

board: prepare build/board/macropad-preview.png build/board/macropad-preview.svg

build/board/macropad-preview.png build/board/macropad-preview.svg &: $(PCB) $(DESIGN_INPUTS) tools/render_board.py tools/appearance.py tools/paths.py build/generated/pcb_geometry.json
	$(PYTHON) tools/render_board.py

all: check board

clean:
	rm -rf build
