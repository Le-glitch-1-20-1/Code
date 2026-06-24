/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_input-05.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:36:37 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 22:53:19 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	handle_no_ctrl_misc(t_app *app)
{
	t_key_config	*k;

	k = &app->keys;
	if (IsKeyPressed(k->random))
		handle_key_random(app);
	if (IsKeyPressed(k->save))
		handle_key_save(app);
	if (IsKeyPressed(k->load))
	{
		app->was_running = app->running;
		app->running = false;
		app->screen = SCREEN_LOAD;
	}
}

void	handle_no_ctrl_keys(t_app *app)
{
	t_key_config	*k;

	k = &app->keys;
	if (IsKeyPressed(k->toggle_play))
		app->running = !app->running;
	if (IsKeyPressed(k->step_once) && !app->running)
	{
		simulation_step(&app->map);
		app->generation++;
	}
	if (IsKeyPressed(k->toggle_grid))
		app->show_grid = !app->show_grid;
	if (IsKeyPressed(k->toggle_hud))
		app->show_hud = !app->show_hud;
	if (IsKeyPressed(k->toggle_chunk_debug))
		app->show_chunk_debug = !app->show_chunk_debug;
	if (IsKeyPressed(k->next_theme))
		app->theme_idx = (app->theme_idx + 1) % THEME_COUNT;
}
