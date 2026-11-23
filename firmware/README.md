# Custom firmware

This folder is the starting point for software running on the macropad. Put implementation code in `src/`. [`board.json`](board.json) records the current board wiring without tying it to a language or SDK. There is no firmware implementation, build target or installed toolchain assumed yet; the root Makefile currently builds the mechanical design and previews.

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

## Starting implementation

A C/C++ implementation can use the official [Raspberry Pi Pico SDK](https://github.com/raspberrypi/pico-sdk) and its [setup guide](https://www.raspberrypi.com/documentation/microcontrollers/c_sdk.html). Start with a custom RP2350-family board definition matching this hardware. RP2354 has 2 MB of internal flash; use that device's configuration rather than copying the Pico 2's external-flash setup. See Raspberry Pi's [RP2350 hardware design guide](https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008280-DS-2-hardware-design-with-rp2350.pdf).

When choosing the toolchain, keep SDK/toolchain versions documented here and keep their build output under `../build/firmware/`. Add configure, build and flash commands only once they work for this board. Keep SDK dependencies within this project or in an explicitly configured SDK location, rather than depending on another project under `/home/am/Dev`.

Bring up one feature at a time:

1. Confirm USB boot mode and load a minimal RP2354A-compatible image.
2. Read GPIO7–12 with pull-ups; confirm all six keys and their physical positions.
3. Add debounce and separate press/release events before binding actions.
4. Add USB HID keyboard reports. Raspberry Pi's [composite HID example](https://github.com/raspberrypi/pico-examples/tree/master/usb/device/dev_hid_composite) is a reference; test both press and release so keys cannot stick.
5. Drive a single dim LED on GPIO6, then verify the full chain. See the SDK's [PIO WS2812 example](https://github.com/raspberrypi/pico-examples/tree/master/pio/ws2812).
6. Scan the display bus on GPIO4/5 and add the confirmed display driver.
7. Add macro mappings, profiles and persistence as those features become useful.

Keep pin definitions, input scanning, USB reports and application actions separate as they grow. Start with a small implementation; add directories when there is code to put in them.

## Flashing and recovery

For the first hardware check, hold SW7 while connecting USB, then release it once the ROM boot device appears. Alternatively, hold SW7, press and release SW8, then release SW7. This sequence follows the boot/reset wiring above and still needs confirmation on the assembled hardware. Use the ROM USB interface with an image built for this board; never flash an arbitrary Pico or RP2040 image. Raspberry Pi documents [USB boot mode and UF2 loading](https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html).

After wiring changes, update `board.json` and the table above from the PCB, then update the implementation's pin constants. The CAD checks do not validate firmware or physical hardware behaviour.
