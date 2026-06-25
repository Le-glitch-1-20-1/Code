/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_screens-5b.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:05:42 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 11:23:02 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	draw_frame(t_app *app)
{
	t_color_theme	th;
	t_renderer		opts;

	th = get_theme(app->theme_idx);
	BeginDrawing();
	ClearBackground(th.bg);
	opts.show_grid = app->show_grid;
	opts.show_chunk_debug = app->show_chunk_debug;
	opts.theme_idx = app->theme_idx;
	renderer_draw(&app->map, app->cam, &opts);
	draw_selections(app);
	draw_frame_screens(app);
	EndDrawing();
}

void	update(t_app *app, float dt)
{
	int		alive;
	int		idx;
	float	td;

	if (app->screen != SCREEN_GAME)
		return ;
	handle_game_input(app);
	if (!app->running)
		return ;
	app->tick_acc += dt;
	td = 1.0f / app->speed;
	while (app->tick_acc >= td)
	{
		simulation_step(&app->map);
		app->generation++;
		app->tick_acc -= td;
		alive = map_alive_count(&app->map);
		idx = app->pop_count % POP_HISTORY_LEN;
		app->pop_history[idx] = alive;
		app->pop_count++;
		if (alive > app->pop_max)
			app->pop_max = alive;
	}
}
