/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_draw.c                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:33:57 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/17 07:33:58 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"
#include "raylib.h"
#include "renderer.h"
#include "save.h"
#include <math.h>

void	draw_selection_info_box(const char *title, int x0, int y0,
	int x1, int y1, int alive)
{
	char	info1[80];
	char	info2[80];
	int		pw;
	int		ph;

	if (x1 >= x0)
		pw = abs(x1 - x0) + 1;
	else
		pw = 0;
	if (y1 >= y0)
		ph = abs(y1 - y0) + 1;
	else
		ph = 0;
	snprintf(info1, sizeof(info1), "%s : %d x %d", title, pw, ph);
	snprintf(info2, sizeof(info2), "Cellules : %d", alive);
	DrawRectangle(10, 50, 240, 50, (Color){14, 14, 22, 210});
	DrawRectangleLinesEx((Rectangle){10, 50, 240, 50}, 1.5f,
		(Color){127, 119, 221, 180});
	DrawText(info1, 18, 58, 15, (Color){200, 200, 255, 240});
	DrawText(info2, 18, 78, 15, (Color){200, 200, 255, 240});
}

void	stamp_pattern(t_app *app, int ox, int oy)
{
	t_chunk_node	*n;
	const t_chunk	*c;
	int				bi;
	int				lx;
	int				ly;

	bi = 0;
	n = map_first(&app->place_map, &bi);
	while (n)
	{
		c = &n->chunk;
		ly = 0;
		while (ly < CHUNK_SIZE)
		{
			if (c->cells[ly])
			{
				lx = 0;
				while (lx < CHUNK_SIZE)
				{
					if (chunk_get(c, lx, ly))
						set_cell_global(&app->map,
							c->cx * CHUNK_SIZE + lx + ox,
							c->cy * CHUNK_SIZE + ly + oy, 1);
					lx++;
				}
			}
			ly++;
		}
		n = map_next(&app->place_map, &bi, n);
	}
}

static void	draw_place_preview_cells(t_app *app, int gx, int gy, float cs)
{
	t_chunk_node	*n;
	const t_chunk	*c;
	int				bi;
	int				lx;
	int				ly;

	bi = 0;
	n = map_first(&app->place_map, &bi);
	while (n)
	{
		c = &n->chunk;
		ly = 0;
		while (ly < CHUNK_SIZE)
		{
			if (c->cells[ly])
			{
				lx = 0;
				while (lx < CHUNK_SIZE)
				{
					if (chunk_get(c, lx, ly))
						DrawRectangleRec((Rectangle){
							(c->cx * CHUNK_SIZE + lx + gx)
							* app->cam.zoom + app->cam.offset.x,
							(c->cy * CHUNK_SIZE + ly + gy)
							* app->cam.zoom + app->cam.offset.y,
							cs, cs}, (Color){221, 185, 60, 160});
					lx++;
				}
			}
			ly++;
		}
		n = map_next(&app->place_map, &bi, n);
	}
}

static void	draw_place_preview_rect(t_app *app, int x0, int y0,
	int x1, int y1, int gx, int gy)
{
	float	sx;
	float	sy;
	float	rw;
	float	rh;

	sx = (x0 + gx) * app->cam.zoom + app->cam.offset.x;
	sy = (y0 + gy) * app->cam.zoom + app->cam.offset.y;
	rw = (x1 - x0 + 1) * app->cam.zoom;
	rh = (y1 - y0 + 1) * app->cam.zoom;
	DrawRectangle((int)sx, (int)sy, (int)rw, (int)rh,
		(Color){221, 185, 60, 40});
	DrawRectangleLinesEx((Rectangle){sx, sy, rw, rh}, 2.0f,
		(Color){221, 185, 60, 200});
}

void	draw_place_preview(t_app *app)
{
	int		x0;
	int		y0;
	int		x1;
	int		y1;
	Vector2	mouse;
	int		gx;
	int		gy;
	float	cs;

	mouse = GetMousePosition();
	gx = (int)floorf((mouse.x - app->cam.offset.x) / app->cam.zoom);
	gy = (int)floorf((mouse.y - app->cam.offset.y) / app->cam.zoom);
	map_bounding_box(&app->place_map, &x0, &y0, &x1, &y1);
	if (x0 > x1)
		return ;
	draw_place_preview_rect(app, x0, y0, x1, y1, gx, gy);
	cs = app->cam.zoom - 1.0f;
	draw_place_preview_cells(app, gx, gy, cs);
}
