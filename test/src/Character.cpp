#include "Character.hpp"
#include "Hitbox.hpp"

Character::Character() {
	sprite = {0, 0, 0, 0};
	coords_far = {0, 0};
}

Character::Character(float x, float y, float width, float height) {
	sprite = {x, y, width, height};
	coords_far = {x + width, y + height};
}

void Character::shift(Vector2 coords) {
	sprite.x += coords.x;
	sprite.y += coords.y;
	coords_far.x += coords.x;
	coords_far.y += coords.y;

	confine();
}

void Character::chase(Character &target) {
	if (sprite.x <= target.sprite.x) {
		shift({speed, 0});
	}
	if (coords_far.x > target.coords_far.x) {
		shift({-speed, 0});
	}
	if (sprite.y <= target.sprite.y) {
		shift({0, speed});
	}
	if (coords_far.y > target.coords_far.y) {
		shift({0, -speed});
	}
}

void Character::set(Vector2 coords) {
	sprite.x = coords.x;
	sprite.y = coords.y;
	coords_far.x = coords.x + sprite.width;
	coords_far.y = coords.y + sprite.height;
}

void Character::confine() {
	float width = GetScreenWidth();
	float height = GetScreenHeight();
	if (sprite.x < 0) {
		set({0, sprite.y});
	}
	if (coords_far.x > width) {
		set({width-sprite.width, sprite.y});
	}
	if (sprite.y < 0) {
		set({sprite.x, 0});
	}
	if (coords_far.y > height) {
		set({sprite.x, height-sprite.height});
	}
}

Rectangle Character::attack(int dir) {
	direction = dir;
	Rectangle res;
	if (dir == 1) {
		res = {sprite.x - 20, sprite.y - 40, sprite.width + 40, 40};
	}
	
	if (dir == 2) {
		res = {sprite.x - 40, sprite.y - 20, 40, sprite.height + 40};
	}
	
	if (dir == 3) {
		res = {sprite.x - 20, coords_far.y, sprite.width + 40, 40};
	}
	
	if (dir == 4) {
		res = {coords_far.x, sprite.y - 20, 40, sprite.height + 40};
	}

	Hitbox(res, 1, *this);
	
	return res;
}

bool Character::takeDamage(int dmg) {
	hp -= dmg;
	if (hp <= 0) {
		hp = 0;
		return true;
	}
	return false;
}
