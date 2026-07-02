/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_screens-8.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/27 21:05:20 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 21:05:20 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	get_rand_bounds(t_app *app, t_rect *out)
{
	if (app->rand_state.x0 < app->rand_state.x1)
		out->xa = app->rand_state.x0;
	else
		out->xa = app->rand_state.x1;
	if (app->rand_state.x0 > app->rand_state.x1)
		out->xb = app->rand_state.x0;
	else
		out->xb = app->rand_state.x1;
	if (app->rand_state.y0 < app->rand_state.y1)
		out->ya = app->rand_state.y0;
	else
		out->ya = app->rand_state.y1;
	if (app->rand_state.y0 > app->rand_state.y1)
		out->yb = app->rand_state.y0;
	else
		out->yb = app->rand_state.y1;
}

static void	draw_rand_rect(t_rect r, t_camera2d_gol cam)
{
	float	sx;
	float	sy;
	float	rw;
	float	rh;

	sx = r.xa * cam.zoom + cam.offset.x;
	sy = r.ya * cam.zoom + cam.offset.y;
	rw = (r.xb - r.xa + 1) * cam.zoom;
	rh = (r.yb - r.ya + 1) * cam.zoom;
	DrawRectangle((int)sx, (int)sy, (int)rw, (int)rh,
		(Color){221, 185, 60, 40});
	DrawRectangleLinesEx((Rectangle){sx, sy, rw, rh}, 2.0f,
		(Color){221, 185, 60, 200});
}

void	draw_screen_random_sel(t_app *app)
{
	t_rect	r;
	int		alive;

	get_rand_bounds(app, &r);
	draw_rand_rect(r, app->cam);
	alive = (int)((r.xb - r.xa + 1) * (r.yb - r.ya + 1)
			* app->rand_state.density);
	draw_selection_info_box((t_sel_box){"Hasard", r.xa, r.ya,
		r.xb, r.yb, alive});
}
