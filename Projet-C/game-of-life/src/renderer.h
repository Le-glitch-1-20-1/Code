/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   renderer.h                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:24:24 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 22:12:07 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef RENDERER_H
# define RENDERER_H

# include "main.h"
# include "chunk.h"

# define THEME_COUNT 5

typedef struct s_color_theme
{
	const char	*name;
	Color		bg;
	Color		cell;
	Color		grid;
}	t_color_theme;

typedef struct s_camera2d_gol
{
	Vector2	offset;
	float	zoom;
}	t_camera2d_gol;

typedef struct s_view_bounds
{
	int	cx_min;
	int	cx_max;
	int	cy_min;
	int	cy_max;
}	t_view_bounds;

typedef struct s_draw_style
{
	float				cell_px;
	const t_color_theme	*th;
	int					show_dbg;
}	t_draw_style;

typedef struct s_render_opts
{
	int	show_grid;
	int	show_chunk_debug;
	int	theme_idx;
}	t_render_opts;

// renderer_chunk.c
void			draw_chunk_cells(const t_chunk *c, t_camera2d_gol cam,
					const t_draw_style *st, Vector2 base);
void			renderer_draw_chunk(const t_chunk *c, t_camera2d_gol cam,
					const t_draw_style *st);
void			rdraw_chunks(const t_chunk_map *map, t_camera2d_gol cam,
					const t_draw_style *st, const t_view_bounds *b);
Color			get_chunk_dbg_color(void);

// renderer_coords.c
Vector2			screen_to_cell(t_camera2d_gol cam, Vector2 screen);
Vector2			cell_to_screen(t_camera2d_gol cam, float cx, float cy);

// renderer_draw.c
void			draw_crosshair(t_camera2d_gol cam);
void			renderer_draw(const t_chunk_map *map, t_camera2d_gol cam,
					const t_render_opts *opts);
t_view_bounds	compute_view_bounds(t_camera2d_gol cam);

// renderer_grid.c
void			rdraw_grid_cols(t_camera2d_gol cam, const t_color_theme *th,
					const t_view_bounds *b);
void			rdraw_grid_rows(t_camera2d_gol cam, const t_color_theme *th,
					const t_view_bounds *b);
void			renderer_draw_grid(t_camera2d_gol cam, const t_color_theme *th,
					const t_view_bounds *b);

// renderer_theme-1.c
void			theme_violet(t_color_theme *t);
void			theme_vert(t_color_theme *t);
void			theme_ambre(t_color_theme *t);
void			theme_cyan(t_color_theme *t);

// renderer_theme-2.c
void			theme_blanc(t_color_theme *t);
t_color_theme	get_theme(int idx);

#endif
