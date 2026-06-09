/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.c                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/03 15:57:02 by le-glitch         #+#    #+#             */
/*   Updated: 2026/05/03 15:57:03 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"
#include "raylib.h"
#include <stdlib.h>
#include <time.h>

int	main(void)
{
	t_app	*app;
	float	dt;

	srand((unsigned)time(NULL));
	SetConfigFlags(FLAG_WINDOW_RESIZABLE | FLAG_VSYNC_HINT);
	InitWindow(1600, 900, "Jeu de la Vie");
	SetTargetFPS(60);
	SetExitKey(0);
	app = app_init();
	if (!app)
	{
		CloseWindow();
		return (1);
	}
	while (!WindowShouldClose())
	{
		dt = GetFrameTime();
		update(app, dt);
		draw_frame(app);
	}
	app_cleanup(app);
	CloseWindow();
	return (0);
}
