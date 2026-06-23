/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   renderer_grid.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:24:24 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 07:27:49 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "renderer.h"

#include "main.h"

void	rdraw_grid_cols(t_camera2d_gol cam,
	const t_color_theme *th, const t_view_bounds *b)
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
			x = cx * CHUNK_SIZE * cam.zoom + cam.offset.x
				+ lx * cam.zoom;
			DrawLineV((Vector2){x, 0},
				(Vector2){x, GetScreenHeight()}, th->grid);
			lx++;
		}
		cx++;
	}
}

void	rdraw_grid_rows(t_camera2d_gol cam,
	const t_color_theme *th, const t_view_bounds *b)
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
			y = cy * CHUNK_SIZE * cam.zoom + cam.offset.y
				+ ly * cam.zoom;
			DrawLineV((Vector2){0, y},
				(Vector2){GetScreenWidth(), y}, th->grid);
			ly++;
		}
		cy++;
	}
}

void	renderer_draw_grid(t_camera2d_gol cam,
	const t_color_theme *th, const t_view_bounds *b)
{
	rdraw_grid_cols(cam, th, b);
	rdraw_grid_rows(cam, th, b);
}
