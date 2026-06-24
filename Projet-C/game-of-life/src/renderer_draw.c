/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   renderer_draw.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:24:24 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 23:05:30 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "renderer.h"

static t_view_bounds	compute_view_bounds(t_camera2d_gol cam)
{
	t_view_bounds	b;
	int				sw;
	int				sh;

	sw = GetScreenWidth();
	sh = GetScreenHeight();
	b.cx_min = (int)floorf((-cam.offset.x) / (CHUNK_SIZE * cam.zoom)) - 1;
	b.cx_max = (int)ceilf((sw - cam.offset.x) / (CHUNK_SIZE * cam.zoom)) + 1;
	b.cy_min = (int)floorf((-cam.offset.y) / (CHUNK_SIZE * cam.zoom)) - 1;
	b.cy_max = (int)ceilf((sh - cam.offset.y) / (CHUNK_SIZE * cam.zoom)) + 1;
	return (b);
}

void	draw_crosshair(t_camera2d_gol cam)
{
	Color	c;

	if (cam.zoom < 3.0f)
		return ;
	c = (Color){255, 80, 80, 120};
	DrawLineV((Vector2){cam.offset.x - 6, cam.offset.y},
		(Vector2){cam.offset.x + 6, cam.offset.y}, c);
	DrawLineV((Vector2){cam.offset.x, cam.offset.y - 6},
		(Vector2){cam.offset.x, cam.offset.y + 6}, c);
}

static void	renderer_prepare(t_camera2d_gol cam, t_renderer *r)
{
	int	idx;

	idx = r->theme_idx;
	if (idx < 0 || idx >= THEME_COUNT)
		idx = 0;
	r->th = get_theme(idx);
	if (cam.zoom >= 4.0f)
		r->cell_px = cam.zoom - 1.0f;
	else
		r->cell_px = cam.zoom;
}

void	renderer_draw(const t_chunk_map *map, t_camera2d_gol cam,
			t_renderer *r)
{
	t_view_bounds	b;

	renderer_prepare(cam, r);
	b = compute_view_bounds(cam);
	if (r->show_grid && cam.zoom >= 4.0f)
		renderer_draw_grid(cam, r, &b);
	rdraw_chunks(map, cam, r, &b);
	draw_crosshair(cam);
}
