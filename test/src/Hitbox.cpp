#include "Hitbox.hpp"

Hitbox::Hitbox(int dmg, Character &org) {
	Posbox = {0, 0, 0, 0};
	Damage = dmg;
	origin = &org;
}

Hitbox::Hitbox(float x, float y, float width, float height, int dmg, Character &org) {
	Posbox = {x, y, width, height};
	Damage = dmg;
	origin = &org;
}

Hitbox::Hitbox(Rectangle coords, int dmg, Character &org) {
	Posbox = {coords.x, coords.y, coords.width, coords.height};
	Damage = dmg;
	origin = &org;
}

Rectangle Hitbox::getPosbox() {
	return Posbox;
}

int Hitbox::getDamage() {
	return Damage;
}