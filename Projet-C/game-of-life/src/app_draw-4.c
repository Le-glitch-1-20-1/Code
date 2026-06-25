/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_draw-1b.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:33:57 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 11:27:42 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	draw_place_preview_rect(t_app *app, t_prev_rect r)
{
	float	sx;
	float	sy;
	float	rw;
	float	rh;

	sx = (r.x0 + r.gx) * app->cam.zoom + app->cam.offset.x;
	sy = (r.y0 + r.gy) * app->cam.zoom + app->cam.offset.y;
	rw = (r.x1 - r.x0 + 1) * app->cam.zoom;
	rh = (r.y1 - r.y0 + 1) * app->cam.zoom;
	DrawRectangle((int)sx, (int)sy, (int)rw, (int)rh,
		(Color){221, 185, 60, 40});
	DrawRectangleLinesEx((Rectangle){sx, sy, rw, rh}, 2.0f,
		(Color){221, 185, 60, 200});
}

void	draw_place_preview(t_app *app)
{
	t_prev_ctx	ctx;
	t_bbox		box;

	ctx.mouse = GetMousePosition();
	ctx.gx = (int)floorf((ctx.mouse.x - app->cam.offset.x) / app->cam.zoom);
	ctx.gy = (int)floorf((ctx.mouse.y - app->cam.offset.y) / app->cam.zoom);
	map_bounding_box(&app->place_map, &box);
	ctx.x0 = box.x0;
	ctx.y0 = box.y0;
	ctx.x1 = box.x1;
	ctx.y1 = box.y1;
	if (ctx.x0 > ctx.x1)
		return ;
	draw_place_preview_rect(app, (t_prev_rect){ctx.x0, ctx.y0,
		ctx.x1, ctx.y1, ctx.gx, ctx.gy});
	ctx.cs = app->cam.zoom - 1.0f;
	draw_place_preview_cells(app, ctx.gx, ctx.gy, ctx.cs);
}
