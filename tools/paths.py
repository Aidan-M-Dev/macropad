"""Project paths shared by the development tools, independent of the working directory."""
import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
CASE = PROJECT / "case"
ACCESSORIES = PROJECT / "accessories"
PCB = PROJECT / "hardware" / "IC Hack Macro Pad.kicad_pcb"
BUILD = PROJECT / "build"
GENERATED = BUILD / "generated"

os.environ.setdefault("MPLCONFIGDIR", str(BUILD / "cache" / "matplotlib"))
