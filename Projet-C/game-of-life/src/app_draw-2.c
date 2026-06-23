/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_draw-2.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:31:09 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 09:07:53 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

int	count_cells_in_rect(t_app *app, int xa, int ya, int xb, int yb)
{
	int	count;
	int	x;
	int	y;

	count = 0;
	y = ya;
	while (y <= yb)
	{
		x = xa;
		while (x <= xb)
		{
			if (get_cell_global(&app->map, x, y))
				count++;
			x++;
		}
		y++;
	}
	return (count);
}

void	draw_select_overlay(t_app *app, int xa, int ya,
	int xb, int yb, const char *title, Color fill, Color border)
{
	float	sx;
	float	sy;
	float	rw;
	float	rh;
	int		count;

	sx = xa * app->cam.zoom + app->cam.offset.x;
	sy = ya * app->cam.zoom + app->cam.offset.y;
	rw = (xb - xa + 1) * app->cam.zoom;
	rh = (yb - ya + 1) * app->cam.zoom;
	DrawRectangleRec((Rectangle){sx, sy, rw, rh}, fill);
	DrawRectangleLinesEx((Rectangle){sx, sy, rw, rh}, 2.0f, border);
	count = count_cells_in_rect(app, xa, ya, xb, yb);
	draw_selection_info_box(title, xa, ya, xb, yb, count);
}

void	minmax_clear(t_app *app, int *xa, int *ya, int *xb, int *yb)
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

void	draw_selections_clear(t_app *app)
{
	int	xa;
	int	ya;
	int	xb;
	int	yb;

	if (!app->clear_select_mode)
		return ;
	if (!app->clear_select_drag)
	{
		draw_selection_info_box("Effacer", 0, 0, -1, -1, 0);
		return ;
	}
	minmax_clear(app, &xa, &ya, &xb, &yb);
	draw_select_overlay(app, xa, ya, xb, yb, "Effacer",
		(Color){220, 50, 50, 55}, (Color){255, 80, 80, 230});
}
