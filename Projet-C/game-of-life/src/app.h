/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app.h                                              :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:01:17 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 12:00:00 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef APP_H
# define APP_H

# include "main.h"
# include "chunk.h"
# include "config.h"
# include "renderer.h"
# include "save.h"
# include "simulation.h"
# include "ui.h"

# define CONFIG_FILE		"keys.cfg"
# define PAN_SPEED			6.0f
# define ZOOM_MIN			2.0f
# define ZOOM_MAX			128.0f
# define POP_HISTORY_LEN	240
# define UNDO_LEN			20

typedef struct s_sel_box
{
	const char	*title;
	int			x0;
	int			y0;
	int			x1;
	int			y1;
	int			alive;
}	t_sel_box;

typedef struct s_rect
{
	int	xa;
	int	ya;
	int	xb;
	int	yb;
}	t_rect;

typedef struct s_bresenham
{
	int	dx;
	int	dy;
	int	sx;
	int	sy;
	int	err;
}	t_bresenham;

typedef struct s_overlay_style
{
	const char	*title;
	Color		fill;
	Color		border;
}	t_overlay_style;

typedef struct s_prev_rect
{
	int	x0;
	int	y0;
	int	x1;
	int	y1;
	int	gx;
	int	gy;
}	t_prev_rect;

typedef struct s_prev_ctx
{
	Vector2	mouse;
	int		x0;
	int		y0;
	int		x1;
	int		y1;
	int		gx;
	int		gy;
	float	cs;
}	t_prev_ctx;

typedef struct s_chunk_draw
{
	int		gx;
	int		gy;
	float	cs;
}	t_chunk_draw;

typedef struct s_app
{
	t_chunk_map			map;
	t_camera2d_gol		cam;
	t_key_config		keys;
	t_screen			screen;
	bool				running;
	bool				was_running;
	bool				menu_just_opened;
	float				speed;
	float				tick_acc;
	int					generation;
	bool				drawing;
	int					draw_val;
	int					last_gx;
	int					last_gy;
	bool				show_grid;
	bool				show_hud;
	bool				show_chunk_debug;
	bool				mid_panning;
	Vector2				mid_pan_origin;
	Vector2				cam_origin;
	t_chunk_map			place_map;
	t_place_state		place_state;
	bool				place_loaded;
	t_random_state		rand_state;
	t_save_zone_state	save_zone;
	bool				clear_select_mode;
	bool				clear_select_drag;
	int					clear_x0;
	int					clear_y0;
	int					clear_x1;
	int					clear_y1;
	bool				copy_select_mode;
	bool				copy_select_drag;
	int					copy_x0;
	int					copy_y0;
	int					copy_x1;
	int					copy_y1;
	t_chunk_map			clipboard;
	bool				clipboard_valid;
	bool				paste_mode;
	int					theme_idx;
	int					pop_history[POP_HISTORY_LEN];
	int					pop_count;
	int					pop_max;
	t_chunk_map			undo_stack[UNDO_LEN];
	bool				undo_valid[UNDO_LEN];
	int					undo_head;
	int					undo_count;
}	t_app;

// app_draw-1.c
void	draw_selection_info_box(t_sel_box b);
void	stamp_pattern(t_app *app, int ox, int oy);
void	draw_place_preview_cells(t_app *app, int gx, int gy, float cs);
void	draw_preview_chunk(t_app *app, const t_chunk *c, t_chunk_draw d);
void	stamp_chunk(t_app *app, const t_chunk *c, int ox, int oy);

// app_draw-2.c
void	draw_select_overlay(t_app *app, t_rect r, t_overlay_style style);
void	minmax_clear(t_app *app, t_rect *out);
void	draw_selections_clear(t_app *app);
int		count_cells_in_rect(t_app *app, t_rect r);

// app_draw-3.c
void	minmax_copy(t_app *app, t_rect *out);
void	draw_selections_copy(t_app *app);
void	draw_selections(t_app *app);

// app_draw-4.c
void	draw_place_preview_rect(t_app *app, t_prev_rect r);
void	draw_place_preview(t_app *app);

// app_init.c
void	app_init_defaults(t_app *app);
void	app_init_undo(t_app *app);
void	app_cleanup(t_app *app);
t_app	*app_init(void);

// app_input-1.c
void	apply_zoom(t_app *app, float wheel);
void	handle_pan_keys(t_app *app);
void	handle_pan_mouse(t_app *app, Vector2 mouse);
void	handle_pan(t_app *app);

// app_input-2.c
void	handle_drawing_start(t_app *app, int gx, int gy);
void	handle_drawing_move(t_app *app, int gx, int gy);
void	handle_drawing(t_app *app, Vector2 mouse, bool on_ui);
void	apply_random_fill(t_chunk_map *map, const t_random_state *rs);

// app_input-3.c
void	get_clear_bounds(t_app *app, t_rect *out);
void	clear_select_apply(t_app *app);
void	handle_clear_select(t_app *app, Vector2 mouse, bool on_ui);
void	get_copy_bounds(t_app *app, t_rect *out);
void	copy_select_fill(t_app *app, t_rect r);

// app_input-4.c
void	ctrl_paste(t_app *app);
void	handle_ctrl_undo_copy(t_app *app);
void	handle_ctrl_shortcuts(t_app *app);
int		handle_escape(t_app *app, bool ctrl);

// app_input-5.c
void	handle_key_random(t_app *app);
void	handle_key_save(t_app *app);
void	handle_no_ctrl_clear(t_app *app);
void	handle_no_ctrl_center(t_app *app);
void	handle_no_ctrl(t_app *app);

// app_input-6.c
void	handle_speed(t_app *app);
void	handle_game_zoom_pan(t_app *app, Vector2 *mouse, bool *on_ui);
void	handle_game_input(t_app *app);

// app_input-7.c
void	draw_line_cells(t_chunk_map *map, t_rect r, int val);
int		bresenham_sx(int x0, int x1);
int		bresenham_sy(int y0, int y1);

// app_input-8.c
void	copy_select_apply(t_app *app);
void	handle_copy_select(t_app *app, Vector2 mouse, bool on_ui);

// app_input-9.c
void	handle_no_ctrl_misc(t_app *app);
void	handle_no_ctrl_keys(t_app *app);

// app_map-1.c
void	center_map_row(t_chunk_map *tmp, const t_chunk *c, int cx, int cy);
void	center_map_iter(t_chunk_map *m, t_chunk_map *tmp, int cx, int cy);
void	center_map(t_chunk_map *m);
int		get_center(int a, int b);

// app_map-2.c
int		save_zone_rle(const char *path, const t_chunk_map *src, t_rect r);

// app_map-3.c
void	rotate_chunk(t_chunk_map *dst, const t_chunk *c);
void	rotate_map_90(const t_chunk_map *src, t_chunk_map *dst);

// app_screens-1.c
void	toolbar_act_clear(t_app *app);
void	toolbar_act_save(t_app *app);
void	toolbar_act_paste(t_app *app);
void	handle_toolbar_act1(t_app *app, t_ui_action act);
void	handle_toolbar_toggle(t_app *app, t_ui_action act);

// app_screens-2.c
void	fill_pop_buf(t_app *app, int *pbuf, int *pn);
void	draw_screen_game_hud(t_app *app);
void	draw_screen_game(t_app *app);

// app_screens-8.c
void	get_rand_bounds(t_app *app, t_rect *out);
void	draw_screen_random_sel(t_app *app);

// app_screens-3.c
void	handle_toolbar_select(t_app *app, t_ui_action act);
void	handle_toolbar_act2(t_app *app, t_ui_action act);
void	handle_toolbar_action(t_app *app, t_ui_action act);

// app_screens-4.c
void	handle_random_result(t_app *app);
void	draw_screen_random(t_app *app);
void	draw_screen_save_zone_rect(t_app *app);
void	draw_screen_save_zone(t_app *app);
void	handle_save_zone_ready(t_app *app, const char *out_path);

// app_screens-5.c
void	handle_load_chosen(t_app *app, const char *out_path);
void	draw_screen_load(t_app *app);
void	draw_frame_menu(t_app *app);
void	draw_frame_screens(t_app *app);

// app_screens-6.c
void	draw_screen_place_rotate(t_app *app);
void	draw_place_info(t_app *app, int gx, int gy);
void	handle_place_drop(t_app *app, Vector2 mpos, int gx, int gy);
void	draw_screen_place(t_app *app);

// app_screens-7.c
void	draw_frame(t_app *app);
void	update(t_app *app, float dt);

// app_undo.c
void	push_undo(t_app *app);
void	pop_undo(t_app *app);

#endif
