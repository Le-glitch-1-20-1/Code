/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_browser-1.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:04:57 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/25 08:29:46 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

void	browser_load_files(char names[MAX_RLE][128], int *count)
{
	const char		*dirs[2];
	DIR				*dir;
	struct dirent	*e;
	int				d;
	int				l;

	dirs[0] = "assets/patterns";
	dirs[1] = "saves";
	*count = 0;
	d = 0;
	while (d < 2)
	{
		dir = opendir(dirs[d]);
		if (dir)
		{
			e = readdir(dir);
			while (e && *count < MAX_RLE)
			{
				l = (int)strlen(e->d_name);
				if (l > 4 && strcmp(e->d_name + l - 4, ".rle") == 0)
					snprintf(names[(*count)++], 128, "%s/%s",
						dirs[d], e->d_name);
				e = readdir(dir);
			}
			closedir(dir);
		}
		d++;
	}
}

int	browser_filter(char names[MAX_RLE][128], int count, int *filtered,
		const char *search)
{
	int			fcount;
	int			i;
	int			j;
	int			dl;
	int			sl;
	char		dlow[128];
	char		slow[64];
	const char	*slash;
	const char	*dname;

	fcount = 0;
	i = 0;
	while (i < count)
	{
		if (!search[0])
		{
			filtered[fcount++] = i;
		}
		else
		{
			slash = strrchr(names[i], '/');
			if (slash)
				dname = slash + 1;
			else
				dname = names[i];
			dl = (int)strlen(dname);
			sl = (int)strlen(search);
			j = 0;
			while (j < dl && j < 127)
			{
				dlow[j] = tolower((unsigned char)dname[j]);
				j++;
			}
			if (dl < 127)
				dlow[dl] = 0;
			else
				dlow[127] = 0;
			j = 0;
			while (j < sl && j < 63)
			{
				slow[j] = tolower((unsigned char)search[j]);
				j++;
			}
			if (sl < 63)
				slow[sl] = 0;
			else
				slow[63] = 0;
			if (strstr(dlow, slow))
				filtered[fcount++] = i;
		}
		i++;
	}
	return (fcount);
}

void	draw_rle_preview_cells(t_chunk_map *map, Rectangle dest, t_bbox box)
{
	t_chunk	*node;
	int		bi;
	int		ly;
	int		lx;
	float	scx;
	float	scy;
	float	scale;
	float	ox;
	float	oy;
	float	cw;

	scx = (dest.width - 8.0f) / (float)(box.x1 - box.x0 + 1);
	scy = (dest.height - 8.0f) / (float)(box.y1 - box.y0 + 1);
	if (scx < scy)
		scale = scx;
	else
		scale = scy;
	if (scale < 0.1f)
		scale = 0.1f;
	ox = dest.x + 4 + ((dest.width - 8)
		- (box.x1 - box.x0 + 1) * scale) * 0.5f;
	oy = dest.y + 4 + ((dest.height - 8)
		- (box.y1 - box.y0 + 1) * scale) * 0.5f;
	if (scale < 1.0f)
		cw = 1.0f;
	else
		cw = scale;
	BeginScissorMode((int)dest.x, (int)dest.y,
		(int)dest.width, (int)dest.height);
	bi = 0;
	node = map_first(map, &bi);
	while (node)
	{
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
							ox + (node->cx * CHUNK_SIZE + lx - box.x0)
								* scale,
							oy + (node->cy * CHUNK_SIZE + ly - box.y0)
								* scale,
							cw, cw}, C_HI);
					lx++;
				}
			}
			ly++;
		}
		node = map_next(map, &bi, node);
	}
	EndScissorMode();
}

bool	load_preview_cache(const char *path, char *cached_path,
			t_chunk_map *cached_map)
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
	(void)cached_path;
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
		cache_valid = load_preview_cache(path, cached_path, &cached_map);
	}
	if (!cache_valid)
	{
		text_c("vide", FS - 2, dest.x + dest.width / 2,
			dest.y + dest.height / 2, C_DIM);
		return ;
	}
	map_bounding_box(&cached_map, &box);
	if (box.x1 - box.x0 + 1 <= 0 || box.y1 - box.y0 + 1 <= 0)
		return ;
	DrawRectangleRec(dest, (Color){10, 10, 15, 255});
	DrawRectangleLinesEx(dest, 1.0f, C_BORDER);
	draw_rle_preview_cells(&cached_map, dest, box);
}
