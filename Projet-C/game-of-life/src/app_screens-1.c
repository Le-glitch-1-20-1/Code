/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_screens-1.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:24:54 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 09:08:31 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

static void	toolbar_act_clear(t_app *app)
{
	push_undo(app);
	map_free(&app->map);
	map_init(&app->map);
	app->generation = 0;
	app->drawing = false;
	app->running = false;
	app->pop_count = 0;
	app->pop_max = 0;
}

static void	toolbar_act_save(t_app *app)
{
	app->was_running = app->running;
	app->running = false;
	app->save_zone = (t_save_zone_state){0};
	snprintf(app->save_zone.name_buf,
		sizeof(app->save_zone.name_buf), "mon_pattern");
	app->screen = SCREEN_SAVE_ZONE;
}

void	toolbar_act_paste(t_app *app)
{
	if (!app->clipboard_valid)
		return ;
	if (app->place_loaded)
		map_free(&app->place_map);
	map_init(&app->place_map);
	map_copy(&app->place_map, &app->clipboard);
	center_map(&app->place_map);
	app->place_state = (t_place_state){0};
	app->place_loaded = true;
	app->copy_select_mode = false;
	app->clear_select_mode = false;
	app->paste_mode = false;
	app->was_running = app->running;
	app->running = false;
	app->screen = SCREEN_PLACE;
}

void	handle_toolbar_act1(t_app *app, t_ui_action act)
{
	if (act == UI_ACTION_PLAY)
		app->running = !app->running;
	else if (act == UI_ACTION_STEP && !app->running)
	{
		simulation_step(&app->map);
		app->generation++;
	}
	else if (act == UI_ACTION_CLEAR)
		toolbar_act_clear(app);
	else if (act == UI_ACTION_OPEN_SAVE)
		toolbar_act_save(app);
	else if (act == UI_ACTION_OPEN_LOAD)
	{
		app->was_running = app->running;
		app->running = false;
		app->screen = SCREEN_LOAD;
	}
	else if (act == UI_ACTION_RANDOM)
	{
		app->was_running = app->running;
		app->running = false;
		app->rand_state = (t_random_state){0};
		app->rand_state.density = 0.3f;
		app->screen = SCREEN_RANDOM;
	}
}

void	handle_toolbar_toggle(t_app *app, t_ui_action act)
{
	if (act == UI_ACTION_TOGGLE_GRID)
		app->show_grid = !app->show_grid;
	else if (act == UI_ACTION_TOGGLE_HUD)
		app->show_hud = !app->show_hud;
	else if (act == UI_ACTION_TOGGLE_CHUNK_DEBUG)
		app->show_chunk_debug = !app->show_chunk_debug;
	else if (act == UI_ACTION_NEXT_THEME)
		app->theme_idx = (app->theme_idx + 1) % THEME_COUNT;
}
