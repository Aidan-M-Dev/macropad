#pragma once

#include <stdint.h>

class Adafruit_SSD1306;

namespace paddle {
enum class Game { None, Pong, Breakout };

void start(Game game, uint32_t now);
void serve(uint32_t now);
void update(Adafruit_SSD1306 &display, uint32_t now, bool left, bool right);
}
