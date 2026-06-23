/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_input-4.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:36:37 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 09:08:11 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	handle_key_random(t_app *app);
void	handle_key_save(t_app *app);

int	handle_escape(t_app *app, bool ctrl)
{
	if (!IsKeyPressed(KEY_ESCAPE))
		return (0);
	if (app->clear_select_mode)
	{
		app->clear_select_mode = false;
		app->clear_select_drag = false;
		return (1);
	}
	if (app->copy_select_mode)
	{
		app->copy_select_mode = false;
		app->copy_select_drag = false;
		return (1);
	}
	if (!ctrl)
	{
		app->was_running = app->running;
		app->running = false;
		app->screen = SCREEN_MENU;
		app->menu_just_opened = true;
	}
	return (1);
}

static void	ctrl_paste(t_app *app)
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

void	handle_ctrl_shortcuts(t_app *app)
{
	t_key_config	*k;

	k = &app->keys;
	if (IsKeyPressed(k->undo))
	{
		app->running = false;
		pop_undo(app);
	}
	if (IsKeyPressed(k->copy))
	{
		app->running = false;
		app->copy_select_mode = true;
		app->copy_select_drag = false;
		app->clear_select_mode = false;
		app->paste_mode = false;
	}
	if (IsKeyPressed(k->paste))
		ctrl_paste(app);
	if (IsKeyPressed(k->clear_zone))
	{
		app->running = false;
		app->clear_select_mode = true;
		app->clear_select_drag = false;
		app->copy_select_mode = false;
		app->paste_mode = false;
	}
}

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
