/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_input-4.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:36:37 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 15:32:01 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

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

void	ctrl_paste(t_app *app)
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

void	handle_ctrl_undo_copy(t_app *app)
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
}

void	handle_ctrl_shortcuts(t_app *app)
{
	t_key_config	*k;

	k = &app->keys;
	handle_ctrl_undo_copy(app);
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
