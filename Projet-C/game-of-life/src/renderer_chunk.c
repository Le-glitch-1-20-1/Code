/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   renderer_chunk.c                                   :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:24:24 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 07:27:38 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "renderer.h"

#include "main.h"

Color	get_chunk_dbg_color(void)
{
	return ((Color){60, 60, 80, 80});
}

static void	draw_chunk_cells(const t_chunk *c, t_camera2d_gol cam,
	const t_draw_style *st, Vector2 base)
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
						base.x + lx * cam.zoom,
						base.y + ly * cam.zoom,
						st->cell_px, st->cell_px}, st->th->cell);
				lx++;
			}
		}
		ly++;
	}
}

void	renderer_draw_chunk(const t_chunk *c, t_camera2d_gol cam,
	const t_draw_style *st)
{
	Vector2	base;

	base.x = c->cx * CHUNK_SIZE * cam.zoom + cam.offset.x;
	base.y = c->cy * CHUNK_SIZE * cam.zoom + cam.offset.y;
	draw_chunk_cells(c, cam, st, base);
	if (st->show_dbg)
		DrawRectangleLinesEx((Rectangle){base.x, base.y,
			CHUNK_SIZE * cam.zoom, CHUNK_SIZE * cam.zoom},
			1.0f, get_chunk_dbg_color());
}

void	rdraw_chunks(const t_chunk_map *map, t_camera2d_gol cam,
	const t_draw_style *st, const t_view_bounds *b)
{
	const t_chunk	*c;
	int				cy;
	int				cx;

	cy = b->cy_min;
	while (cy <= b->cy_max)
	{
		cx = b->cx_min;
		while (cx <= b->cx_max)
		{
			c = map_get(map, cx, cy);
			if (c)
				renderer_draw_chunk(c, cam, st);
			cx++;
		}
		cy++;
	}
}
