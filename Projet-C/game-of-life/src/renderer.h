/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   renderer.h                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:24:24 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:19:38 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef RENDERER_H
# define RENDERER_H

# include "raylib.h"
# include "chunk_map.h"
# include <math.h>

# define THEME_COUNT 5
# define COLOR_CHUNK_DBG (Color){60, 60, 80, 80}

/*
** Theme de couleurs.
*/
typedef struct s_color_theme
{
	const char	*name;
	Color		bg;
	Color		cell;
	Color		grid;
}	t_color_theme;

static inline t_color_theme	get_theme(int idx)
{
	t_color_theme	t;

	if (idx == 0)
	{
		t.name = "Violet";
		t.bg = (Color){14, 18, 20, 255};
		t.cell = (Color){127, 119, 221, 255};
		t.grid = (Color){35, 35, 40, 255};
	}
	else if (idx == 1)
	{
		t.name = "Vert";
		t.bg = (Color){10, 18, 14, 255};
		t.cell = (Color){72, 200, 120, 255};
		t.grid = (Color){25, 40, 30, 255};
	}
	else if (idx == 2)
	{
		t.name = "Ambre";
		t.bg = (Color){18, 14, 8, 255};
		t.cell = (Color){230, 160, 40, 255};
		t.grid = (Color){40, 35, 20, 255};
	}
	else if (idx == 3)
	{
		t.name = "Cyan";
		t.bg = (Color){8, 16, 20, 255};
		t.cell = (Color){60, 200, 210, 255};
		t.grid = (Color){20, 35, 42, 255};
	}
	else
	{
		t.name = "Blanc";
		t.bg = (Color){20, 20, 26, 255};
		t.cell = (Color){210, 210, 220, 255};
		t.grid = (Color){38, 38, 48, 255};
	}
	return (t);
}

/*
** Camera 2D simplifiee pour le jeu de la vie.
*/
typedef struct s_camera2d_gol
{
	Vector2	offset;
	float	zoom;
}	t_camera2d_gol;

static inline Vector2	screen_to_cell(t_camera2d_gol cam, Vector2 screen)
{
	Vector2	result;

	result.x = (screen.x - cam.offset.x) / cam.zoom;
	result.y = (screen.y - cam.offset.y) / cam.zoom;
	return (result);
}

static inline Vector2	cell_to_screen(t_camera2d_gol cam, float cx, float cy)
{
	Vector2	result;

	result.x = cx * cam.zoom + cam.offset.x;
	result.y = cy * cam.zoom + cam.offset.y;
	return (result);
}

static inline void	rdraw_grid_cols(t_camera2d_gol cam,
	const t_color_theme *th, int cx_min, int cx_max)
{
	int		cx;
	int		lx;
	float	x;

	cx = cx_min;
	while (cx <= cx_max + 1)
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

static inline void	rdraw_grid_rows(t_camera2d_gol cam,
	const t_color_theme *th, int cy_min, int cy_max)
{
	int		cy;
	int		ly;
	float	y;

	cy = cy_min;
	while (cy <= cy_max + 1)
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

static inline void	renderer_draw_grid(t_camera2d_gol cam,
	const t_color_theme *th, int cx_min, int cx_max, int cy_min, int cy_max)
{
	rdraw_grid_cols(cam, th, cx_min, cx_max);
	rdraw_grid_rows(cam, th, cy_min, cy_max);
}

static inline void	renderer_draw_chunk(const t_chunk *c, t_camera2d_gol cam,
	float cell_px, const t_color_theme *th, int show_dbg)
{
	float	base_x;
	float	base_y;
	int		lx;
	int		ly;

	base_x = c->cx * CHUNK_SIZE * cam.zoom + cam.offset.x;
	base_y = c->cy * CHUNK_SIZE * cam.zoom + cam.offset.y;
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
						base_x + lx * cam.zoom,
						base_y + ly * cam.zoom,
						cell_px, cell_px}, th->cell);
				lx++;
			}
		}
		ly++;
	}
	if (show_dbg)
		DrawRectangleLinesEx((Rectangle){base_x, base_y,
			CHUNK_SIZE * cam.zoom, CHUNK_SIZE * cam.zoom},
			1.0f, COLOR_CHUNK_DBG);
}

static inline void	rdraw_chunks(const t_chunk_map *map, t_camera2d_gol cam,
	float cell_px, const t_color_theme *th, int show_dbg,
	int cx_min, int cx_max, int cy_min, int cy_max)
{
	const t_chunk	*c;
	int				cy;
	int				cx;

	cy = cy_min;
	while (cy <= cy_max)
	{
		cx = cx_min;
		while (cx <= cx_max)
		{
			c = map_get(map, cx, cy);
			if (c)
				renderer_draw_chunk(c, cam, cell_px, th, show_dbg);
			cx++;
		}
		cy++;
	}
}

static inline void	renderer_draw(const t_chunk_map *map, t_camera2d_gol cam,
	int show_grid, int show_chunk_debug, int theme_idx)
{
	t_color_theme	th;
	int				sw;
	int				sh;
	int				cx_min;
	int				cx_max;
	int				cy_min;
	int				cy_max;
	float			cell_px;

	if (theme_idx < 0 || theme_idx >= THEME_COUNT)
		theme_idx = 0;
	th = get_theme(theme_idx);
	sw = GetScreenWidth();
	sh = GetScreenHeight();
	cx_min = (int)floorf((-cam.offset.x) / (CHUNK_SIZE * cam.zoom)) - 1;
	cx_max = (int)ceilf((sw - cam.offset.x) / (CHUNK_SIZE * cam.zoom)) + 1;
	cy_min = (int)floorf((-cam.offset.y) / (CHUNK_SIZE * cam.zoom)) - 1;
	cy_max = (int)ceilf((sh - cam.offset.y) / (CHUNK_SIZE * cam.zoom)) + 1;
	if (show_grid && cam.zoom >= 4.0f)
		renderer_draw_grid(cam, &th, cx_min, cx_max, cy_min, cy_max);
	if (cam.zoom >= 4.0f)
		cell_px = cam.zoom - 1.0f;
	else
		cell_px = cam.zoom;
	rdraw_chunks(map, cam, cell_px, &th, show_chunk_debug,
		cx_min, cx_max, cy_min, cy_max);
	if (cam.zoom >= 3.0f)
	{
		DrawLineV((Vector2){cam.offset.x - 6, cam.offset.y},
			(Vector2){cam.offset.x + 6, cam.offset.y},
			(Color){255, 80, 80, 120});
		DrawLineV((Vector2){cam.offset.x, cam.offset.y - 6},
			(Vector2){cam.offset.x, cam.offset.y + 6},
			(Color){255, 80, 80, 120});
	}
}

#endif
