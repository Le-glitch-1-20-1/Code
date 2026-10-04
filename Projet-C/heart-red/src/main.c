/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.c                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: you <you@student.42.fr>                   +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 00:00:00 by you               #+#    #+#             */
/*   Updated: 2026/09/02 00:00:00 by you              ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "heart.h"

static void	init_window(int square, t_heart *heart)
{
	int	pos_x;
	int	pos_y;

	SetConfigFlags(FLAG_WINDOW_UNDECORATED | FLAG_MSAA_4X_HINT);
	InitWindow(square, square, "");
	randomize_position(square, &pos_x, &pos_y);
	SetWindowPosition(pos_x, pos_y);
	heart->cx = square / 2;
	heart->cy = square / 2;
	heart->scale = (square / 2.0f) * 0.85f;
}

static void	run_loop(int square, t_heart *heart)
{
	while (!WindowShouldClose())
	{
		BeginDrawing();
		ClearBackground(BLACK);
		DrawRectangleLinesEx((Rectangle){0, 0, square, square}, 1,
			(Color){100, 0, 0, 255});
		draw_heart_outline(heart);
		EndDrawing();
	}
}

int	main(void)
{
	t_heart	heart;
	int		square;

	square = WINDOW_SIZE;
	heart.resol = HEART_RESOLUTION;
	heart.thickness = 3.0f;
	heart.color = RED;
	heart.points = malloc(sizeof(Vector2) * (heart.resol + 1));
	if (!heart.points)
		return (1);
	init_window(square, &heart);
	SetTargetFPS(60);
	SetExitKey(KEY_ESCAPE);
	run_loop(square, &heart);
	free(heart.points);
	CloseWindow();
	return (0);
}
