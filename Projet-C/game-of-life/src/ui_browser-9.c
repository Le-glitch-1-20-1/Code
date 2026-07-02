/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_browser-9.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/27 21:05:20 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 21:05:20 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

static void	draw_rle_preview_valid(const char *path, Rectangle dest)
{
	static t_chunk_map	cached_map;
	t_bbox				box;

	map_bounding_box(&cached_map, &box);
	if (box.x1 - box.x0 + 1 <= 0 || box.y1 - box.y0 + 1 <= 0)
		return ;
	DrawRectangleRec(dest, (Color){10, 10, 15, 255});
	DrawRectangleLinesEx(dest, 1.0f, ui_c_border());
	draw_rle_preview_cells(&cached_map, dest, box);
	(void)path;
}

void	draw_rle_preview(const char *path, Rectangle dest)
{
	static char			cached_path[256] = "";
	static t_chunk_map	cached_map;
	static bool			cache_valid = false;

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
			dest.y + dest.height / 2}, ui_c_dim());
		return ;
	}
	draw_rle_preview_valid(path, dest);
}
