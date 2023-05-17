#pragma once

#include <string>
/* I use this class to unify all evetualy different controller */

#define KEYBOARD 0;
#define GENERAL_GAMEPAD 1;
/*#define XBOX1_GAMEPAD 2;
#define PS4_GAMEPAD 3;
#define SWITCH_GAMEPAD 4;
#define XBOXSERIES_GAMEPAD 5;
#define PS5_GAMEPAD 6;*/


class Controller {
private:
	std::string type;
	std::string types[2] = {"keyboard", "gamepad"};//, "xbox1", "ps4", "switch", "xboxseries", "ps5"};

public:

	// direction one left stick
	double PressedRightL();
	double pressedLeftL();
	double pressedUpL();
	double pressedDownL();

	// direction two right stick
	double pressedRightR();
	double pressedLeftR();
	double pressedUpR();
	double pressedDownR();

	// d pad 
	bool pressedEast();
	bool pressedWeast();
	bool pressedNorth();
	bool pressedSouth();

	// general purpose buttons
	bool pressedConfirm();
	bool pressedCancel();
	bool pressedOption();

	// control buttons
	bool pressedMenu();
	bool pressedPause();
	Controller(int typen);
	Controller();
	~Controller();
};
/*
if (IsGamepadName(GAMEPAD_PLAYER1, "Xbox Controller")) {

 LeftBall.x += GetGamepadAxisMovement(GAMEPAD_PLAYER1,GAMEPAD_AXIS_LEFT_X)*10;
 LeftBall.y += GetGamepadAxisMovement(GAMEPAD_PLAYER1,GAMEPAD_AXIS_LEFT_Y)*10;

 RightBall.x += GetGamepadAxisMovement(GAMEPAD_PLAYER1,GAMEPAD_AXIS_RIGHT_X)*10;
 RightBall.y += GetGamepadAxisMovement(GAMEPAD_PLAYER1,GAMEPAD_AXIS_RIGHT_Y)*10;

 //IsGamepadButtonDown(GAMEPAD_PLAYER1, GAMEPAD_BUTTON_MIDDLE) (+, -)
 //IsGamepadButtonDown(GAMEPAD_PLAYER1, GAMEPAD_BUTTON_RIGHT_FACE_LEFT) (A, B, X, Y)
 //IsGamepadButtonDown(GAMEPAD_PLAYER1, GAMEPAD_BUTTON_LEFT_FACE_UP) (Dpad)
 //IsGamepadButtonDown(GAMEPAD_PLAYER1, GAMEPAD_BUTTON_LEFT_TRIGGER_1) (L, R)
 //GetGamepadAxisMovement(GAMEPAD_PLAYER1, GAMEPAD_AXIS_LEFT_TRIGGER) (ZL, ZR)
 //GetGamepadAxisMovement(GAMEPAD_PLAYER1, GAMEPAD_AXIS_RIGHT_X) (LEFT, RIGHT STICKS)

 }

 DrawText(
 FormatText("DETECTED AXIS [%i]:",GetGamepadAxisCount(GAMEPAD_PLAYER1)), 10, 50, 10,MAROON);

 for (int i = 0; i < GetGamepadAxisCount(GAMEPAD_PLAYER1); i++) {
 DrawText(FormatText("AXIS %i: %.02f", i,GetGamepadAxisMovement
 (GAMEPAD_PLAYER1, i)), 20, 70 + 20 * i, 10, DARKGRAY);
 }

 DrawText(FormatText("DETECTED BUTTON: %i",GetGamepadButtonPressed()), 10, 430, 10, RED);

 } else {
 DrawText("GP1: NOT DETECTED", 10, 10, 10, GRAY);
 }
*/