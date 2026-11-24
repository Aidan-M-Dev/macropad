# Custom firmware

This folder contains the firmware supplied in `firmware.zip`: a USB keyboard with OLED and key LEDs, Pong, Breakout, and a bundled Doom port. The imported source and build files are unchanged from the download. PlatformIO's cached libraries, intermediate build files and macOS metadata were excluded. [`board.json`](board.json) and the board notes below were already in this repository.

| Path | Contents |
| --- | --- |
| [`src/main.cpp`](src/main.cpp) | Keyboard, display, LEDs and startup game selection |
| [`src/paddle.cpp`](src/paddle.cpp) | Pong and Breakout |
| [`include/`](include/) | Pin assignments and game interface |
| [`platformio.ini`](platformio.ini) | PlatformIO environment and dependencies |
| [`doom/`](doom/) | Prebuilt Doom payload, upstream patch and packing/upload scripts |
| [`archive/snake/`](archive/snake/) | Older Snake implementation; not part of the current build |

The root Makefile wraps PlatformIO with `make firmware`; `make all` also builds firmware alongside the mechanical design and previews. This import has not been rebuilt or verified on hardware here.

## Using the supplied firmware

With USB/OLED at the top, the keyboard layout is:

```text
    I   C   H
    A   C   K
```

Hold both keys in a column while connecting USB or resetting to select a game: left (`I` + `A`) for Breakout, middle (both `C` keys) for Pong, right (`H` + `K`) for Doom. Release the keys after startup. In Pong and Breakout, `I` and `H` move the paddle, `K` serves/retries, and `A` exits. Reset with all keys released to return to keyboard mode.

## Building

The supplied configuration uses PlatformIO, the Earle Philhower Arduino core for RP2350, TinyUSB, and Adafruit display/LED libraries. It sets a 2 MB flash limit for this board. Dependencies are declared in [`platformio.ini`](platformio.ini); PlatformIO keeps downloaded libraries and build output in `firmware/.pio/`, which is ignored by Git.

On Ubuntu, install the prerequisites and use the official [PlatformIO installer](https://docs.platformio.org/en/latest/core/installation/methods/installer-script.html) as your normal user:

```bash
sudo apt update
sudo apt install python3-venv curl git
curl -fsSL -o /tmp/get-platformio.py https://raw.githubusercontent.com/platformio/platformio-core-installer/master/get-platformio.py
python3 /tmp/get-platformio.py
export PATH="$HOME/.platformio/penv/bin:$PATH"
pio --version
```

Add the `export PATH` line to your shell startup file to keep it available in new terminals. Alternatively, use `make PIO="$HOME/.platformio/penv/bin/pio" firmware`. The first build downloads the configured toolchain, framework and libraries.

With PlatformIO installed, run from the repository root:

```bash
make firmware
```

This builds `firmware/.pio/build/ichack/ichack-combined.uf2`, containing the keyboard, Pong, Breakout and the bundled Doom payload. Copy that combined UF2 to the RP2350 boot drive using the procedure below. The smaller `firmware.uf2` contains the keyboard/Pong/Breakout application only; it does not supply the Doom payload.

The firmware target invokes `pio run -d firmware -e ichack -t combined`. `make firmware-clean` removes `firmware/.pio/build/` while retaining downloaded dependencies; `make clean` also removes the root `build/` output. The Make command wiring has been checked, but a real firmware build and upload have not been run here.

### Rebuilding Doom

The full upstream Doom source is not included. [`doom/ichack.patch`](doom/ichack.patch) contains the board-specific changes and build instructions for [Smallest Doom](https://github.com/GorGylka/Smallest-Doom) at commit `e176ccb7a444e686b0fd6eb9c31ba09627d14157`. Its header also identifies the Pico SDK and Pico Extras revisions used by the supplier. Rebuilding requires that upstream checkout, the patch, SDK/Extras, the ARM cross-compiler and `picotool`.

[`doom/doom_tiny.bin`](doom/doom_tiny.bin) is retained because the combined build consumes it directly. Follow the patch header to rebuild and replace this payload when changing Doom; the normal PlatformIO build does not rebuild Doom from source.

## Board reference

The source of truth is [`../hardware/IC Hack Macro Pad.kicad_pcb`](../hardware/IC%20Hack%20Macro%20Pad.kicad_pcb) and its schematic. The PCB identifies U1 as **RP2354A**, with a 12 MHz crystal. GPIO numbers below are chip GPIO numbers, not package pad numbers or Pico header positions.

| Function | GPIO | PCB net / component |
| --- | --- | --- |
| OLED SDA | 4 | `/SDA`, U2 pin 4 |
| OLED SCL | 5 | `/SCL`, U2 pin 3 |
| Addressable LED data | 6 | `/LEDin`, D1 DIN |
| SW1 | 7 | `/SW1` |
| SW2 | 8 | `/SW2` |
| SW3 | 9 | `/SW3` |
| SW4 | 10 | `/SW4` |
| SW5 | 11 | `/SW5` |
| SW6 | 12 | `/SW6` |
| Additional labelled signal | 20 | `/ser` |
| Additional labelled signal | 21 | `/Sclk` |
| Additional labelled signal | 22 | `/Rclk` |

Each key connects its GPIO directly to ground when pressed. Configure pull-ups, read low as pressed, and debounce each key independently; there is no row/column matrix in this design.

Viewed from the user side with USB/OLED at the top:

```text
       USB / OLED
    SW1   SW2   SW3
    SW4   SW5   SW6
```

The LED chain is D1 → D2 → D3 → D4 → D5 → D6, corresponding to that same key order. The PCB names the parts WS2812B-2020-V6 and powers them from 3.3 V. Verify colour order and usable brightness on the actual board.

U2's schematic symbol describes a 128×32 SSD1306 I²C module. The mechanical reference separately identifies HS91L02W2C01; confirm the fitted display, controller and I²C address before selecting a driver. Start with an I²C scan rather than assuming an address. The `/ser`, `/Sclk` and `/Rclk` labels are recorded for completeness, not assigned a software role here.

SW7 connects to QSPI chip select through the boot-selection circuit; SW8 connects to RUN. These are the inferred BOOTSEL and reset buttons, respectively, from the PCB connectivity. Confirm their labels on the assembled board. SWDIO and SWCLK are marked unconnected in the current PCB, so an exposed debug header is not available in this design.

## SDK references

For lower-level changes, consult the official [Raspberry Pi Pico SDK](https://github.com/raspberrypi/pico-sdk), its [setup guide](https://www.raspberrypi.com/documentation/microcontrollers/c_sdk.html), and the [RP2350 hardware design guide](https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008280-DS-2-hardware-design-with-rp2350.pdf). RP2354 has 2 MB of internal flash; retain that limit when changing the build configuration. Keep SDK dependencies within this project or in an explicitly configured SDK location, rather than depending on another project under `/home/am/Dev`.

## Flashing and recovery

Hold BOOTSEL (SW7) while connecting USB, then release it once the **RP2350** drive appears. Boot mode was confirmed during this import: the drive reported `UF2 Bootloader v1.1`, model and board ID `RP2350`. Alternatively, the board wiring supports holding SW7, pressing and releasing reset (SW8), then releasing SW7; that alternative sequence has not been checked here.

Copy `ichack-combined.uf2` onto the RP2350 drive and wait for the copy to finish. The drive should disappear as the firmware starts. Use an image built for this board; never flash an arbitrary Pico or RP2040 image. Raspberry Pi documents [USB boot mode and UF2 loading](https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html). Successful flashing and game operation have not yet been confirmed here.

After wiring changes, update `board.json` and the table above from the PCB, then update the implementation's pin constants. The CAD checks do not validate firmware or physical hardware behaviour.
