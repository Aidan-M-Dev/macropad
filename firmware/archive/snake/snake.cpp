#include "snake.h"

#include <Adafruit_SSD1306.h>
#include <Arduino.h>

#include <algorithm>
#include <array>

namespace snake {
namespace {
constexpr int columns = 21;
constexpr int rows = 7;
constexpr int cellSize = 4;
constexpr int capacity = columns * rows;
constexpr int initialLength = 3;
constexpr uint32_t stepMs = 230;

struct Cell {
    int x;
    int y;

    bool operator==(const Cell &other) const {
        return x == other.x && y == other.y;
    }
};

enum class State { Playing, Lost, Won };

std::array<Cell, capacity> body;
Cell food;
int length;
Direction direction;
Direction nextDirection;
State state;
uint32_t lastStep;
bool needsRedraw;

void placeFood() {
    long freeCellsToSkip = random(capacity - length);
    const auto bodyEnd = body.begin() + length;

    for (int y = 0; y < rows; ++y){
        for (int x = 0; x < columns; ++x){
            const Cell cell{x, y};
            if (std::find(body.begin(), bodyEnd, cell) == bodyEnd && freeCellsToSkip-- == 0){
                food = cell;
                return;
            }
        }
    }
}

void move() {
    direction = nextDirection;
    Cell head = body.front();
    switch (direction){
        case Direction::Up: --head.y; break;
        case Direction::Down: ++head.y; break;
        case Direction::Left: --head.x; break;
        case Direction::Right: ++head.x; break;
    }

    const bool grows = head == food;
    // tail moves away unless snake grows
    const auto collisionEnd = body.begin() + length - (grows ? 0 : 1);
    if (head.x < 0 || head.x >= columns || head.y < 0 || head.y >= rows || std::find(body.begin(), collisionEnd, head) != collisionEnd){
        state = State::Lost;
        return;
    }

    length += grows;
    std::move_backward(body.begin(), body.begin() + length - 1, body.begin() + length);
    body.front() = head;

    if (length == capacity){
        state = State::Won;
    }

    else if (grows){
        placeFood();
    }
}

void draw(Adafruit_SSD1306 &display) {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);

    if (state == State::Playing){
        const int boardWidth = columns * cellSize + 4;
        display.drawRect(0, 0, boardWidth, rows * cellSize + 4, SSD1306_WHITE);

        for (int i = 0; i < length; ++i){
            const int size = i == 0 ? cellSize : cellSize - 1;
            display.fillRect(2 + body[i].x * cellSize, 2 + body[i].y * cellSize, size, size, SSD1306_WHITE);
        }

        display.drawRect(2 + food.x * cellSize, 2 + food.y * cellSize, cellSize - 1, cellSize - 1, SSD1306_WHITE);
        display.setCursor(boardWidth + 3, 3);
        display.print(F("SCORE"));
        display.setCursor(boardWidth + 3, 13);
        display.print(length - initialLength);
        display.setCursor(boardWidth + 3, 23);
        display.print(F("K EXIT"));
    }

    else {
        display.setCursor(0, 1);
        display.setTextSize(2);
        display.print(state == State::Won ? F("YOU WIN") : F("GAME OVER"));
        display.setTextSize(1);
        display.setCursor(0, 17);
        display.print(F("SCORE "));
        display.print(length - initialLength);
        display.setCursor(0, 25);
        display.print(F("A RESTART    K EXIT"));
    }

    display.display();
}
}

void start(uint32_t now) {
    length = initialLength;
    for (int i = 0; i < length; ++i){
        body[i] = {columns / 2 - i, rows / 2};
    }

    direction = Direction::Right;
    nextDirection = direction;
    state = State::Playing;
    lastStep = now;
    needsRedraw = true;
    placeFood();
}

void turn(Direction requested) {
    const bool horizontal = direction == Direction::Left || direction == Direction::Right;
    const bool requestedHorizontal = requested == Direction::Left || requested == Direction::Right;
    if (horizontal != requestedHorizontal){
        nextDirection = requested;
    }
}

void update(Adafruit_SSD1306 &display, uint32_t now) {
    if (state == State::Playing && now - lastStep >= stepMs){
        lastStep = now;
        move();
        needsRedraw = true;
    }

    if (needsRedraw){
        draw(display);
        needsRedraw = false;
    }
}
}
