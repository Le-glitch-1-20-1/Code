/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.c                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: replace_me <replace_me@student.42.fr>     +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 00:00:00 by replace_me        #+#    #+#             */
/*   Updated: 2026/09/02 00:00:00 by replace_me       ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "heart.h"

static void	init_window(int square)
{
	int	pwidth;
	int	pheight;

	SetConfigFlags(FLAG_WINDOW_UNDECORATED | FLAG_MSAA_4X_HINT);
	InitWindow(square, square, "");
	randomizer(square, &pwidth, &pheight);
	SetWindowPosition(pwidth, pheight);
}

static void	update_state(float *hue, float *time_offset)
{
	*hue += 1.0f;
	if (*hue >= 360.0f)
		*hue = 0.0f;
	*time_offset += 0.003f;
	if (*time_offset >= 1.0f)
		*time_offset -= 1.0f;
}

static void	render_frame(int square, float hue, t_heart_params *p)
{
	BeginDrawing();
	ClearBackground(BLACK);
	DrawRectangleLinesEx((Rectangle){0, 0, square, square}, 1,
		ColorFromHSV(hue, 1.0f, 1.0f));
	draw_heart_outline(p);
	EndDrawing();
}

int	main(void)
{
	t_heart_params	p;
	float			hue;
	bool			should_close;

	init_window(SQUARE_SIZE);
	p.cx = SQUARE_SIZE / 2;
	p.cy = SQUARE_SIZE / 2;
	p.scale = (SQUARE_SIZE / 2.0f) * 0.85f;
	p.thickness = 3.0f;
	p.time_offset = 0.0f;
	hue = 0.0f;
	should_close = false;
	SetTargetFPS(60);
	SetExitKey(KEY_ESCAPE);
	while (!should_close)
	{
		if (WindowShouldClose())
			should_close = true;
		update_state(&hue, &p.time_offset);
		render_frame(SQUARE_SIZE, hue, &p);
	}
	CloseWindow();
	return (0);
}
