#include "Character.hpp"
#include "raylib.h"

#pragma once

class Hitbox {

private:
	Rectangle Posbox = {0, 0, 0, 0};
	Character *origin;
	int Damage;

public:
	Hitbox(Rectangle coords, int dmg, Character &org);
	Hitbox(float x, float y, float width, float height, int dmg, Character &org);
	Hitbox(int dmg, Character &org);

	Rectangle getPosbox();
	int getDamage();
};