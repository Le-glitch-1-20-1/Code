#include "raylib.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

int	get_random(int min, int max)
{
	return (min + rand() % (max - min + 1));
}

void	resolution(int *Width, int *Height)
{
	*Width = GetMonitorWidth(GetCurrentMonitor());
	*Height = GetMonitorHeight(GetCurrentMonitor());
}

void	randomizer(int Square, int *Pwidth, int *Pheight)
{
	int	Width, Height;

	srand(time(NULL));
	resolution(&Width, &Height);
	*Pwidth = get_random(0, Width - Square);
	*Pheight = get_random(0, Height - Square);
}

void	heart_point(float t, float *x, float *y)
{
	*x = powf(sinf(t), 3);
	*y = -(13 * cosf(t) - 5 * cosf(2 * t) - 2 * cosf(3 * t) - cosf(4 * t)) / 16;
}

// Dessine le contour du coeur avec un degrade de couleur qui tourne le long
// du perimetre, pilote par timeOffset (0.0 a 1.0), comme sur le carre.
void	Draw_heart_outline(int cx, int cy, float scale, float thickness,
		float timeOffset)
{
	Vector2	points[1001];
	float	minx, maxx, miny, maxy;
	float	t, x, y, offx, offy;
	float	hue;
	Color	col;
	int	i;
	int	resol;

	minx = 1e9f; maxx = -1e9f; miny = 1e9f; maxy = -1e9f;
	i = 0;
	resol = 1000;
	while (i <= resol)
	{
		t = (2 * PI * i) / resol;
		heart_point(t, &x, &y);
		if (x < minx) minx = x;
		if (x > maxx) maxx = x;
		if (y < miny) miny = y;
		if (y > maxy) maxy = y;
		i++;
	}
	offx = (minx + maxx) / 2.0f;
	offy = (miny + maxy) / 2.0f;
	i = 0;
	while (i <= resol)
	{
		t = (2 * PI * i) / resol;
		heart_point(t, &x, &y);
		points[i].x = cx + scale * (x - offx);
		points[i].y = cy + scale * (y - offy);
		i++;
	}
	// halo (glow) derriere, meme degrade
	i = 0;
	while (i < resol)
	{
		hue = fmodf(((float)i / resol) + timeOffset, 1.0f) * 360.0f;
		col = ColorFromHSV(hue, 1.0f, 1.0f);
		DrawLineEx(points[i], points[i + 1], thickness + 4.0f, Fade(col, 0.25f));
		i++;
	}
	// trait principal + rond de jonction, meme degrade
	i = 0;
	while (i < resol)
	{
		hue = fmodf(((float)i / resol) + timeOffset, 1.0f) * 360.0f;
		col = ColorFromHSV(hue, 1.0f, 1.0f);
		DrawLineEx(points[i], points[i + 1], thickness, col);
		DrawCircleV(points[i], thickness / 2.0f, col);
		i++;
	}
}

int	main(void)
{
	int		Square = 150;
	int		Pwidth, Pheight;
	float	scale;
	bool	shouldClose;
	float	timeOffset;
	float	hue = 0.0f;

	shouldClose = false;
	timeOffset = 0.0f;
	SetConfigFlags(FLAG_WINDOW_UNDECORATED | FLAG_MSAA_4X_HINT);
	InitWindow(Square, Square, "");

	randomizer(Square, &Pwidth, &Pheight);
	SetWindowPosition(Pwidth, Pheight);

	scale = (Square / 2.0f) * 0.85f;

	SetTargetFPS(60);
	SetExitKey(KEY_ESCAPE);
	while (!shouldClose)
	{
		if (WindowShouldClose())
			shouldClose = true;

        hue += 1.0f;
        if (hue >= 360.0f)
            hue = 0.0f;

		timeOffset += 0.003f; // vitesse de rotation du degrade
		if (timeOffset >= 1.0f)
			timeOffset -= 1.0f;

		BeginDrawing();
			ClearBackground(BLACK);
			DrawRectangleLinesEx((Rectangle){0, 0, Square, Square}, 1, ColorFromHSV(hue, 1.0f, 1.0f));
			Draw_heart_outline(Square / 2, Square / 2, scale, 3.0f, timeOffset);
		EndDrawing();
	}
	CloseWindow();
	return (0);
}
