/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   renderer_chunk.c                                   :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:24:24 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 11:15:03 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "renderer.h"

Color	get_chunk_dbg_color(void)
{
	return ((Color){60, 60, 80, 80});
}

void	draw_chunk_cells(const t_chunk *c, t_camera2d_gol cam,
			const t_renderer *r, Vector2 base)
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
						r->cell_px, r->cell_px}, r->th.cell);
				lx++;
			}
		}
		ly++;
	}
}

void	renderer_draw_chunk(const t_chunk *c, t_camera2d_gol cam,
			const t_renderer *r)
{
	Vector2	base;

	base.x = c->cx * CHUNK_SIZE * cam.zoom + cam.offset.x;
	base.y = c->cy * CHUNK_SIZE * cam.zoom + cam.offset.y;
	draw_chunk_cells(c, cam, r, base);
	if (r->show_chunk_debug)
		DrawRectangleLinesEx((Rectangle){base.x, base.y,
			CHUNK_SIZE * cam.zoom, CHUNK_SIZE * cam.zoom},
			1.0f, get_chunk_dbg_color());
}

static void	rdraw_chunks_row(const t_rdraw_iter *it, int cy,
				const t_view_bounds *b)
{
	const t_chunk	*c;
	int				cx;

	cx = b->cx_min;
	while (cx <= b->cx_max)
	{
		c = map_get(it->map, cx, cy);
		if (c)
			renderer_draw_chunk(c, it->cam, it->r);
		cx++;
	}
}

void	rdraw_chunks(const t_chunk_map *map, t_camera2d_gol cam,
			const t_renderer *r, const t_view_bounds *b)
{
	t_rdraw_iter	it;
	int				cy;

	it = (t_rdraw_iter){map, cam, r};
	cy = b->cy_min;
	while (cy <= b->cy_max)
	{
		rdraw_chunks_row(&it, cy, b);
		cy++;
	}
}
