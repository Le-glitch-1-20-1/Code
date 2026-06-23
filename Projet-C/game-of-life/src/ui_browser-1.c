/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_browser-1.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:04:57 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 23:04:46 by le-glitch        ###   ########.fr       */
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

void	draw_rle_preview_cells(t_chunk_map *map, Rectangle dest, int x0,
			int y0, int x1, int y1)
{
	t_chunk_node	*node;
	const t_chunk	*c;
	int				bi;
	int				ly;
	int				lx;
	float			scx;
	float			scy;
	float			scale;
	float			ox;
	float			oy;
	float			cw;

	scx = (dest.width - 8.0f) / (float)(x1 - x0 + 1);
	scy = (dest.height - 8.0f) / (float)(y1 - y0 + 1);
	if (scx < scy)
		scale = scx;
	else
		scale = scy;
	if (scale < 0.1f)
		scale = 0.1f;
	ox = dest.x + 4 + ((dest.width - 8) - (x1 - x0 + 1) * scale) * 0.5f;
	oy = dest.y + 4 + ((dest.height - 8) - (y1 - y0 + 1) * scale) * 0.5f;
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
		c = &node->chunk;
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
							ox + (c->cx * CHUNK_SIZE + lx - x0) * scale,
							oy + (c->cy * CHUNK_SIZE + ly - y0) * scale,
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

void	draw_rle_preview(const char *path, Rectangle dest)
{
	static char			cached_path[256] = "";
	static t_chunk_map	cached_map;
	static bool			cache_valid = false;
	static bool			cache_err = false;
	int					x0;
	int					y0;
	int					x1;
	int					y1;

	if (strncmp(path, cached_path, sizeof(cached_path) - 1) != 0)
	{
		if (cache_valid)
			map_free(&cached_map);
		cache_valid = false;
		cache_err = false;
		strncpy(cached_path, path, sizeof(cached_path) - 1);
		cached_path[sizeof(cached_path) - 1] = '\0';
		map_init(&cached_map);
		if (load_rle(path, &cached_map, 0, 0) != 0)
		{
			map_free(&cached_map);
			cache_err = true;
		}
		else if (cached_map.chunk_count == 0)
			map_free(&cached_map);
		else
			cache_valid = true;
	}
	if (cache_err)
	{
		text_c("?", FS, dest.x + dest.width / 2,
			dest.y + dest.height / 2, C_DIM);
		return ;
	}
	if (!cache_valid)
	{
		text_c("vide", FS - 2, dest.x + dest.width / 2,
			dest.y + dest.height / 2, C_DIM);
		return ;
	}
	map_bounding_box(&cached_map, &x0, &y0, &x1, &y1);
	if (x1 - x0 + 1 <= 0 || y1 - y0 + 1 <= 0)
		return ;
	DrawRectangleRec(dest, (Color){10, 10, 15, 255});
	DrawRectangleLinesEx(dest, 1.0f, C_BORDER);
	draw_rle_preview_cells(&cached_map, dest, x0, y0, x1, y1);
}

void	browser_draw_search(Rectangle p, int pw, char *search,
			bool *search_edit, int *scroll)
{
	Rectangle	sbox;
	Vector2		mm;
	int			lx3;
	int			sw3;
	int			sw4;
	int			tw;
	int			k;
	int			l;

	DrawText("Recherche:", (int)p.x + 16, (int)p.y + 56, FS, C_DIM);
	lx3 = (int)p.x + 16 + MeasureText("Recherche:", FS) + 8;
	sw3 = pw - 30;
	sw4 = (int)p.x + 16 + sw3 - lx3;
	sbox = (Rectangle){(float)lx3, (float)((int)p.y + 54),
		(float)sw4, (float)(FS + 8)};
	DrawRectangleRec(sbox, C_PANEL2);
	if (*search_edit)
		DrawRectangleLinesEx(sbox, 1.0f, C_HI);
	else
		DrawRectangleLinesEx(sbox, 1.0f, C_BORDER);
	mm = GetMousePosition();
	if (IsMouseButtonReleased(0) && CheckCollisionPointRec(mm, sbox))
		*search_edit = true;
	if (IsMouseButtonReleased(0) && !CheckCollisionPointRec(mm, sbox))
		*search_edit = false;
	if (*search_edit)
	{
		k = GetCharPressed();
		while (k > 0)
		{
			l = (int)strlen(search);
			if (l < 60)
			{
				search[l] = (char)k;
				search[l + 1] = 0;
			}
			k = GetCharPressed();
		}
		if (IsKeyPressed(KEY_BACKSPACE))
		{
			l = (int)strlen(search);
			if (l > 0)
			{
				search[l - 1] = 0;
				*scroll = 0;
			}
		}
	}
	if (search[0])
		DrawText(search, lx3 + 4, (int)p.y + 56, FS, C_TEXT);
	else
		DrawText("...", lx3 + 4, (int)p.y + 56, FS, C_DIM);
	if (*search_edit && (GetTime() * 2 - (int)(GetTime() * 2) < 0.5))
	{
		tw = MeasureText(search, FS);
		DrawText("|", lx3 + 4 + tw, (int)p.y + 56, FS, C_HI);
	}
}
