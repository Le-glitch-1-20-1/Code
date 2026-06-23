/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_screens-3.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:21:42 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 07:26:33 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"
#include "renderer.h"
#include "save.h"
#include "simulation.h"

#include "main.h"

void	toolbar_act_paste(t_app *app);
void	handle_toolbar_act1(t_app *app, t_ui_action act);

void	handle_toolbar_select(t_app *app, t_ui_action act)
{
	if (act == UI_ACTION_COPY_ZONE)
	{
		app->running = false;
		app->copy_select_mode = true;
		app->copy_select_drag = false;
		app->clear_select_mode = false;
		app->paste_mode = false;
	}
	else if (act == UI_ACTION_CLEAR_ZONE)
	{
		app->running = false;
		app->clear_select_mode = true;
		app->clear_select_drag = false;
		app->copy_select_mode = false;
		app->paste_mode = false;
	}
	else if (act == UI_ACTION_PASTE)
		toolbar_act_paste(app);
}

static void	handle_toolbar_act2(t_app *app, t_ui_action act)
{
	if (act == UI_ACTION_MENU)
	{
		app->was_running = app->running;
		app->running = false;
		app->screen = SCREEN_MENU;
	}
	else if (act == UI_ACTION_CENTER)
	{
		app->cam.offset.x = GetScreenWidth() / 2.0f;
		app->cam.offset.y = GetScreenHeight() / 2.0f;
	}
	else if (act == UI_ACTION_UNDO)
	{
		app->running = false;
		pop_undo(app);
	}
	handle_toolbar_toggle(app, act);
	handle_toolbar_select(app, act);
}

void	handle_toolbar_action(t_app *app, t_ui_action act)
{
	handle_toolbar_act1(app, act);
	handle_toolbar_act2(app, act);
}
