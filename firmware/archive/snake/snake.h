#pragma once

#include <stdint.h>

class Adafruit_SSD1306;

namespace snake {
enum class Direction { Up, Down, Left, Right };

void start(uint32_t now);
void turn(Direction direction);
void update(Adafruit_SSD1306 &display, uint32_t now);
}
