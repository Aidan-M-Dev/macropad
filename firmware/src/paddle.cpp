#include "paddle.h"

#include <Adafruit_SSD1306.h>
#include <Arduino.h>

#include <algorithm>

namespace paddle {
namespace {
constexpr int width = 128;
constexpr int height = 32;
constexpr int paddleWidth = 22;
constexpr int paddleY = height - 2;
constexpr int opponentY = 1;
constexpr int ballSize = 2;
constexpr int pongTarget = 5;
constexpr int brickColumns = 8;
constexpr int brickRows = 3;
constexpr uint32_t fullBricks = (1u << (brickColumns * brickRows)) - 1;
constexpr uint32_t stepMs = 24;

enum class State { Ready, Playing, Won, Lost };

Game game;
State state;
int playerX;
int opponentX;
int ballX;
int ballY;
int dx;
int dy;
int playerScore;
int opponentScore;
int lives;
uint32_t bricks;
uint32_t lastStep;
bool needsRedraw;

void resetBall() {
    ballX = playerX + (paddleWidth - ballSize) / 2;
    ballY = paddleY - ballSize;
}

bool hitsPaddle(int x) {
    return ballX + ballSize > x && ballX < x + paddleWidth;
}

void bounceFromPlayer() {
    const int offset = ballX + ballSize / 2 - (playerX + paddleWidth / 2);
    if (offset != 0){
        const int speed = abs(offset) >= paddleWidth / 3 ? 2 : 1;
        dx = offset < 0 ? -speed : speed;
    }

    dy = -1;
}

bool hitBrick(int x, int y) {
    for (int row = 0; row < brickRows; ++row){
        const int top = 2 + row * 4;
        if (y >= top + 3 || y + ballSize <= top){
            continue;
        }

        for (int column = 0; column < brickColumns; ++column){
            const int left = 8 + column * 14;
            const uint32_t bit = 1u << (row * brickColumns + column);
            if ((bricks & bit) && x < left + 12 && x + ballSize > left){
                bricks &= ~bit;
                return true;
            }
        }
    }

    return false;
}

void moveBall() {
    const bool pong = game == Game::Pong;
    const int nextX = ballX + dx;
    if (nextX < 0 || nextX > width - ballSize || (!pong && hitBrick(nextX, ballY))){
        dx = -dx;
    }

    else {
        ballX = nextX;
    }

    const int nextY = ballY + dy;
    if (!pong && (nextY < 0 || hitBrick(ballX, nextY))){
        dy = -dy;
    }

    else if (dy > 0 && nextY + ballSize > paddleY && ballY + ballSize <= paddleY && hitsPaddle(playerX)){
        bounceFromPlayer();
    }

    else if (pong && dy < 0 && nextY < opponentY + 2 && ballY >= opponentY + 2 && hitsPaddle(opponentX)){
        dy = 1;
    }

    else {
        ballY = nextY;
    }

    if (pong && ballY < -ballSize){
        state = ++playerScore == pongTarget ? State::Won : State::Ready;
    }

    else if (ballY >= height){
        const bool lost = pong ? ++opponentScore == pongTarget : --lives == 0;
        state = lost ? State::Lost : State::Ready;
    }

    else if (!pong && bricks == 0){
        state = State::Won;
    }

    if (state == State::Ready){
        resetBall();
    }
}

void draw(Adafruit_SSD1306 &display) {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);

    if (state == State::Won || state == State::Lost){
        display.setTextSize(2);
        display.setCursor(0, 1);
        display.print(state == State::Won ? F("YOU WIN") : F("GAME OVER"));
        display.setTextSize(1);
        display.setCursor(0, 23);
        display.print(F("K RETRY    A EXIT"));
        display.display();
        return;
    }

    if (game == Game::Pong){
        display.fillRect(opponentX, opponentY, paddleWidth, 2, SSD1306_WHITE);
        display.setCursor(1, 5);
        display.print(playerScore);
        display.setCursor(121, 5);
        display.print(opponentScore);
    }

    else {
        for (int row = 0; row < brickRows; ++row){
            for (int column = 0; column < brickColumns; ++column){
                if (bricks & (1u << (row * brickColumns + column))){
                    display.fillRect(8 + column * 14, 2 + row * 4, 12, 3, SSD1306_WHITE);
                }
            }
        }

        for (int i = 0; i < lives; ++i){
            display.fillRect(1 + i * 3, 26, 2, 2, SSD1306_WHITE);
        }
    }

    if (state == State::Ready){
        display.setCursor(43, 16);
        display.print(F("K SERVE"));
    }

    display.fillRect(playerX, paddleY, paddleWidth, 2, SSD1306_WHITE);
    display.fillRect(ballX, ballY, ballSize, ballSize, SSD1306_WHITE);
    display.display();
}
}

void start(Game selectedGame, uint32_t now) {
    game = selectedGame;
    state = State::Ready;
    playerX = (width - paddleWidth) / 2;
    opponentX = playerX;
    playerScore = 0;
    opponentScore = 0;
    lives = 3;
    bricks = fullBricks;
    lastStep = now;
    needsRedraw = true;
    resetBall();
}

void serve(uint32_t now) {
    if (state == State::Won || state == State::Lost){
        start(game, now);
    }

    else if (state == State::Ready){
        dx = playerX < (width - paddleWidth) / 2 ? 1 : -1;
        dy = -1;
        state = State::Playing;
        lastStep = now;
        needsRedraw = true;
    }
}

void update(Adafruit_SSD1306 &display, uint32_t now, bool left, bool right) {
    if ((state == State::Ready || state == State::Playing) && now - lastStep >= stepMs){
        lastStep = now;
        const int nextPlayerX = std::clamp(playerX + 3 * (int(right) - int(left)), 0, width - paddleWidth);
        needsRedraw |= playerX != nextPlayerX;
        playerX = nextPlayerX;

        if (state == State::Playing){
            if (game == Game::Pong){
                const int target = dy < 0 && ballY < height / 2 ? ballX - paddleWidth / 2 : (width - paddleWidth) / 2;
                opponentX = std::clamp(opponentX + std::clamp(target - opponentX, -1, 1), 0, width - paddleWidth);
            }

            moveBall();
            needsRedraw = true;
        }

        else {
            resetBall();
        }
    }

    if (needsRedraw){
        draw(display);
        needsRedraw = false;
    }
}
}
