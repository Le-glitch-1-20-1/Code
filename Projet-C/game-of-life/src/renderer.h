/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   renderer.h                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:24:24 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 11:14:54 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef RENDERER_H
# define RENDERER_H

# include "main.h"
# include "chunk.h"

# define THEME_COUNT 5

/*
** Palette de couleurs d'un thème visuel.
*/
typedef struct s_color_theme
{
	const char	*name;
	Color		bg;
	Color		cell;
	Color		grid;
}	t_color_theme;

/*
** Caméra 2D du jeu : position (offset) et niveau de zoom.
*/
typedef struct s_camera2d_gol
{
	Vector2	offset;
	float	zoom;
}	t_camera2d_gol;

/*
** Bornes en chunks de la zone visible à l'écran.
*/
typedef struct s_view_bounds
{
	int	cx_min;
	int	cx_max;
	int	cy_min;
	int	cy_max;
}	t_view_bounds;

/*
** État complet du renderer pour un frame :
**   - options utilisateur (grille, debug, thème)
**   - données dérivées calculées à chaque frame (cell_px, thème résolu)
*/
typedef struct s_renderer
{
	int				show_grid;
	int				show_chunk_debug;
	int				theme_idx;
	float			cell_px;
	t_color_theme	th;
}	t_renderer;

typedef struct s_rdraw_iter
{
	const t_chunk_map	*map;
	t_camera2d_gol		cam;
	const t_renderer	*r;
}	t_rdraw_iter;

// renderer_chunk.c
void			draw_chunk_cells(const t_chunk *c, t_camera2d_gol cam,
					const t_renderer *r, Vector2 base);
void			renderer_draw_chunk(const t_chunk *c, t_camera2d_gol cam,
					const t_renderer *r);
void			rdraw_chunks(const t_chunk_map *map, t_camera2d_gol cam,
					const t_renderer *r, const t_view_bounds *b);
Color			get_chunk_dbg_color(void);

// renderer_coords.c
Vector2			screen_to_cell(t_camera2d_gol cam, Vector2 screen);
Vector2			cell_to_screen(t_camera2d_gol cam, float cx, float cy);

// renderer_draw.c
void			draw_crosshair(t_camera2d_gol cam);
void			renderer_draw(const t_chunk_map *map, t_camera2d_gol cam,
					t_renderer *r);

// renderer_grid.c
void			renderer_draw_grid(t_camera2d_gol cam, const t_renderer *r,
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
