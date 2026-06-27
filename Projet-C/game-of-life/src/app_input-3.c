/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_input-3.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:19:44 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 15:17:42 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	get_clear_bounds(t_app *app, t_rect *out)
{
	minmax_clear(app, out);
}

void	clear_select_apply(t_app *app)
{
	t_rect	r;
	int		x;
	int		y;

	get_clear_bounds(app, &r);
	push_undo(app);
	y = r.ya;
	while (y <= r.yb)
	{
		x = r.xa;
		while (x <= r.xb)
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

void	get_copy_bounds(t_app *app, t_rect *out)
{
	minmax_copy(app, out);
}

void	copy_select_fill(t_app *app, t_rect r)
{
	int	x;
	int	y;

	map_free(&app->clipboard);
	map_init(&app->clipboard);
	y = r.ya;
	while (y <= r.yb)
	{
		x = r.xa;
		while (x <= r.xb)
		{
			if (get_cell_global(&app->map, x, y))
				set_cell_global(&app->clipboard, x - r.xa, y - r.ya, 1);
			x++;
		}
		y++;
	}
	app->clipboard_valid = true;
	app->copy_select_mode = false;
	app->copy_select_drag = false;
}
