#include "raylib.h"

#pragma once

class Character {
private:
    int hp = 3;
    unsigned char direction; // 1 alto, 2 sinistra, 3 basso, 4 destra

public:
    float speed = 5;
    Rectangle sprite = {0, 0, 0, 0};    // x, y in alto a sinistra larghezza e altezza 
    Vector2 coords_far = {0, 0};        // x, y in basso a destra

    Character(float x, float y, float width, float height);
    Character();

    void shift(Vector2 coords);
    void chase(Character &target);
    void confine();
    void set(Vector2 coords);
    Rectangle attack(int dir);
    bool takeDamage(int dmg);
};