#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
    printf '%s\n' "Usage: sh $0 keyboard.elf doom_tiny.bin combined.uf2" >&2
    exit 2
fi

objcopy=${OBJCOPY:-arm-none-eabi-objcopy}
picotool=${PICOTOOL:-picotool}
doom_offset=$((0x18000))
flash_limit=$((0x1ff000))
temporary=$(mktemp -d "${TMPDIR:-/tmp}/ichack-combine.XXXXXX")
trap 'rm -f "$temporary/keyboard.bin" "$temporary/combined.bin"; rmdir "$temporary"' EXIT

"$objcopy" -O binary "$1" "$temporary/keyboard.bin"
keyboard_size=$(wc -c < "$temporary/keyboard.bin")
doom_size=$(wc -c < "$2")

if [ "$keyboard_size" -gt "$doom_offset" ] || [ "$((doom_offset + doom_size))" -gt "$flash_limit" ]; then
    printf '%s\n' 'Firmware exceeds the combined flash layout.' >&2
    exit 1
fi

"$objcopy" -I binary -O binary --gap-fill 0xff --pad-to "$doom_offset" \
    "$temporary/keyboard.bin" "$temporary/combined.bin"
dd if="$2" of="$temporary/combined.bin" bs=4096 seek="$((doom_offset / 4096))" conv=notrunc 2>/dev/null

"$picotool" uf2 convert -t bin "$temporary/combined.bin" "$3" --family 0xe48bff59 --abs-block
