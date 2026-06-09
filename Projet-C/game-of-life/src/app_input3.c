/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/* app_input3.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/* By: student <student@student.42.fr>              +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/* Created: 2025/01/01 00:00:00 by student           #+#    #+#             */
/* Updated: 2025/01/01 00:00:00 by student          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"
#include "raylib.h"
#include "simulation.h"
#include <math.h>

void	get_clear_bounds(t_app *app, int *xa, int *ya, int *xb, int *yb)
{
	if (app->clear_x0 < app->clear_x1)
		*xa = app->clear_x0;
	else
		*xa = app->clear_x1;
	if (app->clear_y0 < app->clear_y1)
		*ya = app->clear_y0;
	else
		*ya = app->clear_y1;
	if (app->clear_x0 > app->clear_x1)
		*xb = app->clear_x0;
	else
		*xb = app->clear_x1;
	if (app->clear_y0 > app->clear_y1)
		*yb = app->clear_y0;
	else
		*yb = app->clear_y1;
}

static void	clear_select_apply(t_app *app)
{
	int	xa;
	int	ya;
	int	xb;
	int	yb;
	int	x;
	int	y;

	get_clear_bounds(app, &xa, &ya, &xb, &yb);
	push_undo(app);
	y = ya;
	while (y <= yb)
	{
		x = xa;
		while (x <= xb)
		{
			set_cell_global(&app->map, x, y, 0);
			x++;
		}
		y++;
	}
	map_remove_dead(&app->map);
	app->clear_select_mode = false;
	app->clear_select_drag = false;
}

void	handle_clear_select(t_app *app, Vector2 mouse, bool on_ui)
{
	int	gx;
	int	gy;

	if (!app->clear_select_mode || on_ui || app->mid_panning)
		return ;
	gx = (int)floorf((mouse.x - app->cam.offset.x) / app->cam.zoom);
	gy = (int)floorf((mouse.y - app->cam.offset.y) / app->cam.zoom);
	if (IsMouseButtonPressed(MOUSE_BUTTON_LEFT))
	{
		app->clear_select_drag = true;
		app->clear_x0 = gx;
		app->clear_y0 = gy;
		app->clear_x1 = gx;
		app->clear_y1 = gy;
	}
	if (app->clear_select_drag && IsMouseButtonDown(MOUSE_BUTTON_LEFT))
	{
		app->clear_x1 = gx;
		app->clear_y1 = gy;
	}
	if (app->clear_select_drag && IsMouseButtonReleased(MOUSE_BUTTON_LEFT))
		clear_select_apply(app);
}

void	get_copy_bounds(t_app *app, int *xa, int *ya, int *xb, int *yb)
{
	if (app->copy_x0 < app->copy_x1)
		*xa = app->copy_x0;
	else
		*xa = app->copy_x1;
	if (app->copy_y0 < app->copy_y1)
		*ya = app->copy_y0;
	else
		*ya = app->copy_y1;
	if (app->copy_x0 > app->copy_x1)
		*xb = app->copy_x0;
	else
		*xb = app->copy_x1;
	if (app->copy_y0 > app->copy_y1)
		*yb = app->copy_y0;
	else
		*yb = app->copy_y1;
}

void	copy_select_fill(t_app *app, int xa, int ya, int xb, int yb)
{
	int	x;
	int	y;

	map_free(&app->clipboard);
	map_init(&app->clipboard);
	y = ya;
	while (y <= yb)
	{
		x = xa;
		while (x <= xb)
		{
			if (get_cell_global(&app->map, x, y))
				set_cell_global(&app->clipboard, x - xa, y - ya, 1);
			x++;
		}
		y++;
	}
	app->clipboard_valid = true;
	app->copy_select_mode = false;
	app->copy_select_drag = false;
}
