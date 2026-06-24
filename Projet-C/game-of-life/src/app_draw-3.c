/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_draw-3.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:31:09 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 23:04:58 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

int	count_cells_in_rect(t_app *app, t_rect r)
{
	int	count;
	int	x;
	int	y;

	count = 0;
	y = r.ya;
	while (y <= r.yb)
	{
		x = r.xa;
		while (x <= r.xb)
		{
			if (get_cell_global(&app->map, x, y))
				count++;
			x++;
		}
		y++;
	}
	return (count);
}

void	draw_select_overlay(t_app *app, t_rect r, t_overlay_style style)
{
	float	sx;
	float	sy;
	float	rw;
	float	rh;
	int		count;

	sx = r.xa * app->cam.zoom + app->cam.offset.x;
	sy = r.ya * app->cam.zoom + app->cam.offset.y;
	rw = (r.xb - r.xa + 1) * app->cam.zoom;
	rh = (r.yb - r.ya + 1) * app->cam.zoom;
	DrawRectangleRec((Rectangle){sx, sy, rw, rh}, style.fill);
	DrawRectangleLinesEx((Rectangle){sx, sy, rw, rh}, 2.0f, style.border);
	count = count_cells_in_rect(app, r);
	draw_selection_info_box((t_sel_box){style.title, r.xa, r.ya,
		r.xb, r.yb, count});
}

void	minmax_clear(t_app *app, t_rect *out)
{
	if (app->clear_x0 < app->clear_x1)
		out->xa = app->clear_x0;
	else
		out->xa = app->clear_x1;
	if (app->clear_y0 < app->clear_y1)
		out->ya = app->clear_y0;
	else
		out->ya = app->clear_y1;
	if (app->clear_x0 > app->clear_x1)
		out->xb = app->clear_x0;
	else
		out->xb = app->clear_x1;
	if (app->clear_y0 > app->clear_y1)
		out->yb = app->clear_y0;
	else
		out->yb = app->clear_y1;
}

void	draw_selections_clear(t_app *app)
{
	t_rect	r;

	if (!app->clear_select_mode)
		return ;
	if (!app->clear_select_drag)
	{
		draw_selection_info_box((t_sel_box){"Effacer", 0, 0, -1, -1, 0});
		return ;
	}
	minmax_clear(app, &r);
	draw_select_overlay(app, r, (t_overlay_style){"Effacer",
		(Color){220, 50, 50, 55}, (Color){255, 80, 80, 230}});
}
