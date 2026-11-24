#include <Adafruit_NeoPixel.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_TinyUSB.h>
#include <Arduino.h>
#include <Wire.h>
#include <hardware/structs/powman.h>
#include <hardware/structs/scb.h>
#include <hardware/structs/systick.h>
#include <hardware/watchdog.h>
#include <pico/bootrom.h>

#include <algorithm>
#include <array>

#include "paddle.h"
#include "pins.h"

namespace {
constexpr uint32_t debounceMs = 5;
constexpr uint32_t gameStartupWindowMs = 750;
constexpr uint32_t doomFlashAddress = XIP_BASE + 0x18000;
constexpr uint32_t doomFlashSize = 0x1ff000 - 0x18000;
constexpr uint32_t doomWadOffset = 0x2f000;
constexpr uint32_t doomWadMagic = 0x58485749;
constexpr uint32_t doomTraceMagic = 0x444f4f4d;

struct Key {
    uint8_t pin;
    uint8_t code;
    char legend;
    bool rawPressed = false;
    bool pressed = false;
    uint32_t changedAt = 0;
};

Key keys[] = {
    {pins::sw1, HID_KEY_I, 'I'},
    {pins::sw2, HID_KEY_C, 'C'},
    {pins::sw3, HID_KEY_H, 'H'},
    {pins::sw4, HID_KEY_A, 'A'},
    {pins::sw5, HID_KEY_C, 'C'},
    {pins::sw6, HID_KEY_K, 'K'},
};

const uint8_t keyboardDescriptor[] = {TUD_HID_REPORT_DESC_KEYBOARD()};
Adafruit_USBD_HID keyboard(keyboardDescriptor, sizeof(keyboardDescriptor), HID_ITF_PROTOCOL_KEYBOARD, 1, false);
Adafruit_SSD1306 display(128, 32, &Wire, -1);
Adafruit_NeoPixel keyLeds(std::size(keys), pins::ledData, NEO_GRB + NEO_KHZ800);
bool displayReady = false;
paddle::Game activeGame = paddle::Game::None;
bool waitForKeyRelease = false;
bool doomLaunchFailed = false;
char doomTraceStage = 0;
uint32_t doomTraceTic = 0;
uint8_t doomTraceFlags = 0;
uint32_t doomTracePc = 0;
uint32_t doomTraceFault = 0;

void updateKeyLeds() {
    const uint32_t pressedColour = Adafruit_NeoPixel::Color(0, 24, 32);
    // d1 to d6 follow switch order
    for (size_t index = 0; index < std::size(keys); ++index){
        keyLeds.setPixelColor(index, keys[index].pressed ? pressedColour : 0);
    }

    keyLeds.show();
}

void drawDisplay() {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(2);
    display.setCursor(0, 3);
    display.print(F("IC HACK"));
    display.setTextSize(1);
    display.setCursor(0, 23);
    if (doomTraceStage){
        display.print(F("D "));
        display.print(doomTraceStage);
        display.print(' ');
        display.print(doomTraceTic % 10000);
        display.print(' ');
        display.print(doomTraceFlags, HEX);
        display.setCursor(88, 3);
        display.print(doomTracePc ? F("PC") : F("FAULT"));
        display.setCursor(79, 23);
        display.print(doomTracePc ? doomTracePc : doomTraceFault, HEX);
        display.display();
        return;
    }

    else {
        display.print(doomLaunchFailed ? F("DOOM ERROR") : F(":)"));
    }
    display.drawFastVLine(85, 1, 30, SSD1306_WHITE);

    for (size_t index = 0; index < std::size(keys); ++index){
        const Key &key = keys[index];
        const int16_t x = 89 + (index % 3) * 13;
        const int16_t y = (index / 3) * 17;

        if (key.pressed){
            display.fillRoundRect(x, y, 12, 15, 2, SSD1306_WHITE);
        }

        else {
            display.drawRoundRect(x, y, 12, 15, 2, SSD1306_WHITE);
        }

        display.setTextColor(key.pressed ? SSD1306_BLACK : SSD1306_WHITE);
        display.setCursor(x + 3, y + 4);
        display.write(key.legend);
    }

    display.display();
}

void updateKeyboard() {
    static std::array<uint8_t, 6> sentReport{};
    static bool reportSent = false;

    if (!TinyUSBDevice.mounted()){
        reportSent = false;
        return;
    }

    std::array<uint8_t, 6> report{};
    auto nextCode = report.begin();
    for (const Key &key : keys){
        // both c switches share one hid usage
        if (key.pressed && std::find(report.begin(), nextCode, key.code) == nextCode){
            *nextCode++ = key.code;
        }
    }

    if ((!reportSent || report != sentReport) && keyboard.ready() && keyboard.keyboardReport(0, 0, report.data())){
        sentReport = report;
        reportSent = true;
    }
}

bool beginDisplay() {
    for (uint8_t address : {0x3c, 0x3d}){
        Wire.beginTransmission(address);
        if (Wire.endTransmission() == 0){
            return display.begin(SSD1306_SWITCHCAPVCC, address, false, false);
        }
    }

    return false;
}

void selectStartupMode() {
    const uint32_t startedAt = millis();
    uint32_t chordChangedAt = startedAt;
    paddle::Game chordGame = paddle::Game::None;
    paddle::Game requestedGame = paddle::Game::None;

    while (millis() - startedAt < gameStartupWindowMs){
        const uint32_t now = millis();
        paddle::Game heldGame = paddle::Game::None;
        if (digitalRead(pins::sw2) == LOW && digitalRead(pins::sw5) == LOW){
            heldGame = paddle::Game::Pong;
        }

        else if (digitalRead(pins::sw1) == LOW && digitalRead(pins::sw4) == LOW){
            heldGame = paddle::Game::Breakout;
        }

        if (heldGame != chordGame){
            chordGame = heldGame;
            chordChangedAt = now;
        }

        if (!doomTraceStage && chordGame != paddle::Game::None && now - chordChangedAt >= debounceMs){
            requestedGame = chordGame;
        }

        if (!displayReady && beginDisplay()){
            displayReady = true;
            if (requestedGame == paddle::Game::None){
                drawDisplay();
            }
        }

        if (displayReady && requestedGame != paddle::Game::None){
            activeGame = requestedGame;
            waitForKeyRelease = true;
            for (Key &key : keys){
                key.rawPressed = digitalRead(key.pin) == LOW;
                key.pressed = key.rawPressed;
            }

            updateKeyLeds();
            display.clearDisplay();
            display.setTextColor(SSD1306_WHITE);
            display.setTextSize(2);
            display.setCursor(0, 1);
            display.print(activeGame == paddle::Game::Pong ? F("PONG") : F("BREAKOUT"));
            display.setTextSize(1);
            display.setCursor(0, 23);
            display.print(F("RELEASE KEYS"));
            display.display();
            return;
        }

        delay(debounceMs);
    }
}
}

void initVariant() {
    if (powman_hw->scratch[0] == doomTraceMagic){
        doomTraceStage = powman_hw->scratch[1];
        doomTraceTic = powman_hw->scratch[2];
        doomTraceFlags = powman_hw->scratch[3];
        doomTracePc = powman_hw->scratch[4];
        doomTraceFault = powman_hw->scratch[5];
        powman_hw->scratch[0] = 0;
        waitForKeyRelease = true;
        if (watchdog_caused_reboot()){
            return;
        }
    }

    for (uint8_t pin : {pins::sw3, pins::sw6}){
        gpio_init(pin);
        gpio_pull_up(pin);
    }

    sleep_ms(debounceMs);
    if (gpio_get(pins::sw3) || gpio_get(pins::sw6)){
        return;
    }

    sleep_ms(debounceMs);
    if (gpio_get(pins::sw3) || gpio_get(pins::sw6)){
        return;
    }

    // boot rom remaps doom flash window before transferring control
    const auto wadHeader = reinterpret_cast<const volatile uint32_t *>(doomFlashAddress + doomWadOffset);
    if (*wadHeader == doomWadMagic){
        if (keyLeds.begin()){
            keyLeds.clear();
            keyLeds.show();
            sleep_us(500);
        }

        alignas(4) static uint8_t workArea[4096];
        const uint32_t interruptState = save_and_disable_interrupts();
        const uint32_t systickControl = systick_hw->csr;
        // stop arduino systick before doom installs its exception table
        systick_hw->csr = 0;
        scb_hw->icsr = M33_ICSR_PENDSTCLR_BITS;
        __dsb();
        __isb();
        rom_chain_image(workArea, sizeof(workArea), doomFlashAddress, doomFlashSize);
        systick_hw->csr = systickControl;
        restore_interrupts_from_disabled(interruptState);
    }

    doomLaunchFailed = true;
}

void setup() {
    for (const Key &key : keys){
        pinMode(key.pin, INPUT_PULLUP);
    }

    keyboard.begin();
    keyLeds.begin();
    updateKeyLeds();

    Wire.setSDA(pins::oledSda);
    Wire.setSCL(pins::oledScl);
    Wire.begin();

    selectStartupMode();
}

void loop() {
    const uint32_t now = millis();
    bool keysChanged = false;

    for (Key &key : keys){
        const bool pressed = digitalRead(key.pin) == LOW;
        if (pressed != key.rawPressed){
            key.rawPressed = pressed;
            key.changedAt = now;
        }

        if (key.pressed != key.rawPressed && now - key.changedAt >= debounceMs){
            key.pressed = key.rawPressed;
            keysChanged = true;
            if (activeGame != paddle::Game::None && !waitForKeyRelease && key.pressed){
                if (key.pin == pins::sw4){
                    activeGame = paddle::Game::None;
                    waitForKeyRelease = true;
                }

                else if (key.pin == pins::sw6){
                    paddle::serve(now);
                }
            }
        }
    }

    if (waitForKeyRelease && std::none_of(std::begin(keys), std::end(keys), [](const Key &key) { return key.rawPressed || key.pressed; })){
        waitForKeyRelease = false;
        if (activeGame != paddle::Game::None){
            paddle::start(activeGame, now);
        }
    }

    if (activeGame == paddle::Game::None && !waitForKeyRelease){
        updateKeyboard();
    }

    if (keysChanged){
        updateKeyLeds();
    }

    if (activeGame != paddle::Game::None && !waitForKeyRelease){
        paddle::update(display, now, keys[0].pressed, keys[2].pressed);
    }

    else if (activeGame == paddle::Game::None && keysChanged && displayReady){
        drawDisplay();
    }
}
