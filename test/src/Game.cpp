#include <iostream>
#include "raylib.h"
#include "Character.hpp"

void move();
void checkHitboxes();

void Debug(Character c){
	std::cout << "Debug passing";
	return;
}

Character player(100, 100, 100, 100);
Character enemy(700, 700, 100, 100);

Rectangle Hitbox;

int screenWidth = 800;
int screenHeight = 800;
int main(void) {

	// Initialization
	//--------------------------------------------------------------------------------------

	//SetConfigFlags(FLAG_FULLSCREEN_MODE);
	SetTraceLogLevel(LOG_ALL);

	InitWindow(screenWidth, screenHeight, "easy platformer");

	// Debug(player);

	// Load images after Window initialization cuz the openGL context is needed by raylib


	SetTargetFPS(50);         // Set our game to run at 30 frames-per-second
	//--------------------------------------------------------------------------------------

	// Main game loop
	while (!WindowShouldClose()) {    // Detect window close button or ESC key

		// Update --------------------------------------------------------------------------
		//enemy.chase(player);
		move();
		checkHitboxes();

		// Draw ----------------------------------------------------------------------------
		BeginDrawing();
		{
			ClearBackground(WHITE);
			
			DrawRectangleRec(enemy.sprite, {255, 0, 0, 255});
			DrawRectangleRec(player.sprite, {0, 0, 255, 255});
			//DrawRectangleRec(Hitbox, {0, 0, 255, 128});


		}
		EndDrawing();

		
		// Reset variables
		//Hitbox = {0, 0, 0, 0};

	}

	// De-Initialization
	//--------------------------------------------------------------------------------------

	CloseWindow();  // Close window and OpenGL context
	//--------------------------------------------------------------------------------------
	return 0;
}

void move() {
	float speed = player.speed;

	if (IsKeyDown(KEY_A)){
		//system("tcp_client.exe 127.0.0.1");
		player.shift({-speed, 0});
	} else if (IsKeyDown(KEY_D)){
		player.shift({speed, 0});
	}

	if (IsKeyDown(KEY_W)) {
		player.shift({0, -speed});
	} else	if (IsKeyDown(KEY_S)) {
		player.shift({0, speed});
	}

	if (IsKeyPressed(KEY_LEFT)) {
		enemy.shift({-speed, 0});
	} else if (IsKeyPressed(KEY_RIGHT)) {
		enemy.shift({-speed, 0});
	}
	
	if (IsKeyPressed(KEY_UP)) {
		enemy.shift({-speed, 0});
	} else if (IsKeyPressed(KEY_DOWN)) {
		enemy.shift({-speed, 0});
	}

}

void checkHitboxes() {
	bool isDed;
	if (CheckCollisionRecs(enemy.sprite, Hitbox)) {
		isDed = enemy.takeDamage(1);
	}

	if (isDed) {
		enemy = Character(0, 0, 0, 0);
	}

}