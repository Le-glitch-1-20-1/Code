/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   renderer_grid.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:24:24 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 11:09:48 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "renderer.h"

static void	rdraw_grid_cols(t_camera2d_gol cam, const t_renderer *r,
				const t_view_bounds *b)
{
	int		cx;
	int		lx;
	float	x;

	cx = b->cx_min;
	while (cx <= b->cx_max + 1)
	{
		lx = 0;
		while (lx < CHUNK_SIZE)
		{
			x = cx * CHUNK_SIZE * cam.zoom + cam.offset.x + lx * cam.zoom;
			DrawLineV((Vector2){x, 0},
				(Vector2){x, GetScreenHeight()}, r->th.grid);
			lx++;
		}
		cx++;
	}
}

static void	rdraw_grid_rows(t_camera2d_gol cam, const t_renderer *r,
				const t_view_bounds *b)
{
	int		cy;
	int		ly;
	float	y;

	cy = b->cy_min;
	while (cy <= b->cy_max + 1)
	{
		ly = 0;
		while (ly < CHUNK_SIZE)
		{
			y = cy * CHUNK_SIZE * cam.zoom + cam.offset.y + ly * cam.zoom;
			DrawLineV((Vector2){0, y},
				(Vector2){GetScreenWidth(), y}, r->th.grid);
			ly++;
		}
		cy++;
	}
}

void	renderer_draw_grid(t_camera2d_gol cam, const t_renderer *r,
			const t_view_bounds *b)
{
	rdraw_grid_cols(cam, r, b);
	rdraw_grid_rows(cam, r, b);
}
