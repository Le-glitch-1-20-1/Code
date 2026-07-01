/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_draw-1.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:33:57 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 12:00:00 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	draw_selection_info_box(t_sel_box b)
{
	char	info1[80];
	char	info2[80];
	int		pw;
	int		ph;

	if (b.x1 >= b.x0)
		pw = abs(b.x1 - b.x0) + 1;
	else
		pw = 0;
	if (b.y1 >= b.y0)
		ph = abs(b.y1 - b.y0) + 1;
	else
		ph = 0;
	snprintf(info1, sizeof(info1), "%s : %d x %d", b.title, pw, ph);
	snprintf(info2, sizeof(info2), "Cellules : %d", b.alive);
	DrawRectangle(10, 50, 240, 50, (Color){14, 14, 22, 210});
	DrawRectangleLinesEx((Rectangle){10, 50, 240, 50}, 1.5f,
		(Color){127, 119, 221, 180});
	DrawText(info1, 18, 58, 15, (Color){200, 200, 255, 240});
	DrawText(info2, 18, 78, 15, (Color){200, 200, 255, 240});
}

void	stamp_chunk(t_app *app, const t_chunk *c, int ox, int oy)
{
	int	lx;
	int	ly;

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
}

void	stamp_pattern(t_app *app, int ox, int oy)
{
	t_chunk	*n;
	int		bi;

	bi = 0;
	n = map_first(&app->place_map, &bi);
	while (n)
	{
		stamp_chunk(app, n, ox, oy);
		n = map_next(&app->place_map, &bi, n);
	}
}

void	draw_preview_chunk(t_app *app, const t_chunk *c, t_chunk_draw d)
{
	int	lx;
	int	ly;

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
						(c->cx * CHUNK_SIZE + lx + d.gx)
						* app->cam.zoom + app->cam.offset.x,
						(c->cy * CHUNK_SIZE + ly + d.gy)
						* app->cam.zoom + app->cam.offset.y,
						d.cs, d.cs}, (Color){221, 185, 60, 160});
				lx++;
			}
		}
		ly++;
	}
}

void	draw_place_preview_cells(t_app *app, int gx, int gy, float cs)
{
	t_chunk	*n;
	int		bi;

	bi = 0;
	n = map_first(&app->place_map, &bi);
	while (n)
	{
		draw_preview_chunk(app, n, (t_chunk_draw){gx, gy, cs});
		n = map_next(&app->place_map, &bi, n);
	}
}
