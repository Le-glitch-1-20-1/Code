/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app.h                                              :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:01:17 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:03:20 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef APP_H
# define APP_H

# include "raylib.h"
# include "chunk_map.h"
# include "renderer.h"
# include "ui.h"
# include "config.h"
# include <stdbool.h>

# define CONFIG_FILE		"keys.cfg"
# define PAN_SPEED		6.0f
# define ZOOM_MIN		2.0f
# define ZOOM_MAX		128.0f
# define POP_HISTORY_LEN	240
# define UNDO_LEN		20

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

t_app	*app_init(void);
void	app_cleanup(t_app *app);

void	push_undo(t_app *app);
void	pop_undo(t_app *app);

void	center_map(t_chunk_map *m);
void	rotate_map_90(const t_chunk_map *src, t_chunk_map *dst);

void	apply_zoom(t_app *app, float wheel);
void	handle_pan(t_app *app);

void	draw_line_cells(t_chunk_map *map, int x0, int y0, int x1,
			int y1, int val);
void	stamp_pattern(t_app *app, int ox, int oy);
void	apply_random_fill(t_chunk_map *map, const t_random_state *rs);
int		save_zone_rle(const char *path, const t_chunk_map *src,
			int x0, int y0, int x1, int y1);

void	draw_selections(t_app *app);
void	draw_place_preview(t_app *app);
void	draw_selection_info_box(const char *title, int x0, int y0,
			int x1, int y1, int alive);

void	handle_drawing(t_app *app, Vector2 mouse, bool on_ui);
void	handle_clear_select(t_app *app, Vector2 mouse, bool on_ui);
void	handle_copy_select(t_app *app, Vector2 mouse, bool on_ui);
void	handle_no_ctrl(t_app *app);
void	handle_speed(t_app *app);
void	handle_game_input(t_app *app);
void	handle_toolbar_action(t_app *app, t_ui_action act);
void	handle_toolbar_toggle(t_app *app, t_ui_action act);
void	handle_toolbar_select(t_app *app, t_ui_action act);

void	draw_screen_game(t_app *app);
void	draw_screen_random(t_app *app);
void	draw_screen_save_zone(t_app *app);
void	draw_screen_place(t_app *app);
void	draw_screen_load(t_app *app);
void	draw_frame_menu(t_app *app);
void	draw_frame_screens(t_app *app);

void	draw_frame(t_app *app);
void	update(t_app *app, float dt);

/* app_input.c */
int		bresenham_sx(int x0, int x1);
int		bresenham_sy(int y0, int y1);

/* app_input3.c */
void	get_copy_bounds(t_app *app, int *xa, int *ya, int *xb, int *yb);
void	copy_select_fill(t_app *app, int xa, int ya, int xb, int yb);
void	get_clear_bounds(t_app *app, int *xa, int *ya, int *xb, int *yb);

/* app_input4.c */
int		handle_escape(t_app *app, bool ctrl);
void	handle_ctrl_shortcuts(t_app *app);
void	handle_no_ctrl_keys(t_app *app);
void	handle_no_ctrl_misc(t_app *app);

/* app_draw2.c */
int		count_cells_in_rect(t_app *app, int xa, int ya, int xb, int yb);
void	draw_select_overlay(t_app *app, int xa, int ya, int xb, int yb,
			const char *title, Color fill, Color border);
void	minmax_clear(t_app *app, int *xa, int *ya, int *xb, int *yb);
void	minmax_copy(t_app *app, int *xa, int *ya, int *xb, int *yb);
void	draw_selections_clear(t_app *app);

/* app_screens.c */
void	toolbar_act_paste(t_app *app);
void	handle_toolbar_act1(t_app *app, t_ui_action act);

/* app_screens2.c */
void	fill_pop_buf(t_app *app, int *pbuf, int *pn);
void	get_rand_bounds(t_app *app, int *xmin, int *xmax,
			int *ymin, int *ymax);
void	draw_screen_random_sel(t_app *app);
void	draw_screen_save_zone_rect(t_app *app);
void	draw_screen_place_rotate(t_app *app);

#endif
