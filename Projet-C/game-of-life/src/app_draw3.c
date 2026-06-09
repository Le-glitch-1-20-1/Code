/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/* app_draw3.c                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/* By: student <student@student.42.fr>              +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/* Created: 2025/01/01 00:00:00 by student           #+#    #+#             */
/* Updated: 2025/01/01 00:00:00 by student          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"
#include "raylib.h"
#include "renderer.h"
#include <math.h>

void	draw_select_overlay(t_app *app, int xa, int ya,
	int xb, int yb, const char *title, Color fill, Color border);
void	draw_selections_clear(t_app *app);

void	minmax_copy(t_app *app, int *xa, int *ya, int *xb, int *yb)
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

static void	draw_selections_copy(t_app *app)
{
	int	xa;
	int	ya;
	int	xb;
	int	yb;

	if (!app->copy_select_mode)
		return ;
	if (!app->copy_select_drag)
	{
		draw_selection_info_box("Copier", 0, 0, -1, -1, 0);
		return ;
	}
	minmax_copy(app, &xa, &ya, &xb, &yb);
	draw_select_overlay(app, xa, ya, xb, yb, "Copier",
		(Color){50, 120, 220, 45}, (Color){80, 160, 255, 230});
}

void	draw_selections(t_app *app)
{
	draw_selections_clear(app);
	draw_selections_copy(app);
}
