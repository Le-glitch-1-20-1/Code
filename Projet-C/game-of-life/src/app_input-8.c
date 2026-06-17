/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_input8.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:25:15 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/17 07:25:16 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"
#include "raylib.h"
#include "simulation.h"
#include <math.h>

void	get_copy_bounds(t_app *app, int *xa, int *ya, int *xb, int *yb);
void	copy_select_fill(t_app *app, int xa, int ya, int xb, int yb);

static void	copy_select_apply(t_app *app)
{
	int	xa;
	int	ya;
	int	xb;
	int	yb;

	get_copy_bounds(app, &xa, &ya, &xb, &yb);
	copy_select_fill(app, xa, ya, xb, yb);
}

void	handle_copy_select(t_app *app, Vector2 mouse, bool on_ui)
{
	int	gx;
	int	gy;

	if (!app->copy_select_mode || on_ui || app->mid_panning)
		return ;
	gx = (int)floorf((mouse.x - app->cam.offset.x) / app->cam.zoom);
	gy = (int)floorf((mouse.y - app->cam.offset.y) / app->cam.zoom);
	if (IsMouseButtonPressed(MOUSE_BUTTON_LEFT))
	{
		app->copy_select_drag = true;
		app->copy_x0 = gx;
		app->copy_y0 = gy;
		app->copy_x1 = gx;
		app->copy_y1 = gy;
	}
	if (app->copy_select_drag && IsMouseButtonDown(MOUSE_BUTTON_LEFT))
	{
		app->copy_x1 = gx;
		app->copy_y1 = gy;
	}
	if (app->copy_select_drag && IsMouseButtonReleased(MOUSE_BUTTON_LEFT))
		copy_select_apply(app);
}
