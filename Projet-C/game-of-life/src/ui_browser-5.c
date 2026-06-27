/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_browser-5.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:04:57 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 08:35:43 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

t_prev_scale	compute_preview_scale(t_bbox box, Rectangle dest)
{
	t_prev_scale	s;
	float			scx;
	float			scy;

	scx = (dest.width - 8.0f) / (float)(box.x1 - box.x0 + 1);
	scy = (dest.height - 8.0f) / (float)(box.y1 - box.y0 + 1);
	if (scx < scy)
		s.scale = scx;
	else
		s.scale = scy;
	if (s.scale < 0.1f)
		s.scale = 0.1f;
	s.ox = dest.x + 4 + ((dest.width - 8)
		- (box.x1 - box.x0 + 1) * s.scale) * 0.5f;
	s.oy = dest.y + 4 + ((dest.height - 8)
		- (box.y1 - box.y0 + 1) * s.scale) * 0.5f;
	if (s.scale < 1.0f)
		s.cw = 1.0f;
	else
		s.cw = s.scale;
	return (s);
}

void	draw_preview_node(const t_chunk *node, t_bbox box,
				t_prev_scale s)
{
	int	ly;
	int	lx;

	ly = 0;
	while (ly < CHUNK_SIZE)
	{
		if (node->cells[ly])
		{
			lx = 0;
			while (lx < CHUNK_SIZE)
			{
				if (chunk_get(node, lx, ly))
					DrawRectangleRec((Rectangle){
						s.ox + (node->cx * CHUNK_SIZE + lx - box.x0)
							* s.scale,
						s.oy + (node->cy * CHUNK_SIZE + ly - box.y0)
							* s.scale,
						s.cw, s.cw}, C_HI);
				lx++;
			}
		}
		ly++;
	}
}

void	draw_rle_preview_cells(t_chunk_map *map, Rectangle dest, t_bbox box)
{
	t_chunk			*node;
	int				bi;
	t_prev_scale	s;

	s = compute_preview_scale(box, dest);
	BeginScissorMode((int)dest.x, (int)dest.y,
		(int)dest.width, (int)dest.height);
	bi = 0;
	node = map_first(map, &bi);
	while (node)
	{
		draw_preview_node(node, box, s);
		node = map_next(map, &bi, node);
	}
	EndScissorMode();
}

bool	load_preview_cache(const char *path, t_chunk_map *cached_map)
{
	if (load_rle(path, cached_map, 0, 0) != 0)
	{
		map_free(cached_map);
		return (false);
	}
	if (cached_map->chunk_count == 0)
	{
		map_free(cached_map);
		return (false);
	}
	return (true);
}

void	draw_rle_preview(const char *path, Rectangle dest)
{
	static char			cached_path[256] = "";
	static t_chunk_map	cached_map;
	static bool			cache_valid = false;
	t_bbox				box;

	if (strncmp(path, cached_path, sizeof(cached_path) - 1) != 0)
	{
		if (cache_valid)
			map_free(&cached_map);
		strncpy(cached_path, path, sizeof(cached_path) - 1);
		cached_path[sizeof(cached_path) - 1] = '\0';
		map_init(&cached_map);
		cache_valid = load_preview_cache(path, &cached_map);
	}
	if (!cache_valid)
	{
		text_c("vide", FS - 2, (Vector2){dest.x + dest.width / 2,
			dest.y + dest.height / 2}, C_DIM);
		return ;
	}
	map_bounding_box(&cached_map, &box);
	if (box.x1 - box.x0 + 1 <= 0 || box.y1 - box.y0 + 1 <= 0)
		return ;
	DrawRectangleRec(dest, (Color){10, 10, 15, 255});
	DrawRectangleLinesEx(dest, 1.0f, C_BORDER);
	draw_rle_preview_cells(&cached_map, dest, box);
}
