/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_screens-7.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:05:42 by le-glitch         #+#    #+#             */
/*   Updated: 2026/07/11 09:50:00 by le-glitch        ###   ########.fr       */
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

void	track_population(t_app *app)
{
	int	alive;
	int	idx;

	alive = map_alive_count(&app->map);
	idx = app->pop_count % POP_HISTORY_LEN;
	app->pop_history[idx] = alive;
	app->pop_count++;
	if (alive > app->pop_max)
		app->pop_max = alive;
}

void	update(t_app *app, float dt)
{
	float	td;
	int		steps;

	if (app->screen != SCREEN_GAME)
		return ;
	handle_game_input(app);
	if (!app->running)
		return ;
	app->tick_acc += dt;
	td = 1.0f / app->speed;
	steps = run_simulation_steps(app, td);
	if (app->tick_acc > td)
		app->tick_acc = td;
	if (steps > 0)
		track_population(app);
}

int	run_simulation_steps(t_app *app, float td)
{
	int	steps;

	steps = 0;
	while (app->tick_acc >= td && steps < MAX_STEPS_FRAME)
	{
		simulation_step(&app->map);
		app->generation++;
		app->tick_acc -= td;
		steps++;
	}
	return (steps);
}
