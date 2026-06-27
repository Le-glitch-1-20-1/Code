/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui.h                                               :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:01:58 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/25 08:35:42 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef UI_H
# define UI_H

# include "main.h"
# include "chunk.h"
# include "config.h"
# include "renderer.h"
# include "save.h"

# define C_BG		(Color){14,  14,  18,  255}
# define C_PANEL	(Color){24,  24,  34,  245}
# define C_PANEL2	(Color){30,  30,  44,  255}
# define C_BORDER	(Color){55,  55,  80,  255}
# define C_HI		(Color){127, 119, 221, 255}
# define C_TEXT		(Color){210, 210, 225, 255}
# define C_DIM		(Color){100, 100, 125, 255}
# define C_HOVER	(Color){42,  40,  68,  255}
# define C_ACTIVE	(Color){72,  66,  148, 255}
# define C_GREEN	(Color){72,  200, 120, 255}
# define C_YELLOW	(Color){230, 185, 55,  255}
# define C_RED		(Color){210, 72,  72,  255}
# define C_OVERLAY	(Color){0,   0,   0,   195}
# define C_ACCENT2	(Color){80,  195, 145, 255}
# define C_ORANGE	(Color){220, 140, 50,  255}

# define FS			15
# define FM			18
# define FL			24
# define FXL		32
# define MAX_RLE	512
# define KB_N		28

typedef enum e_screen
{
	SCREEN_GAME,
	SCREEN_MENU,
	SCREEN_KEYBINDS,
	SCREEN_CREDITS,
	SCREEN_SAVE,
	SCREEN_SAVE_ZONE,
	SCREEN_LOAD,
	SCREEN_PLACE,
	SCREEN_RANDOM,
}	t_screen;

typedef enum e_btn_state
{
	BTN_IDLE,
	BTN_HOVERED,
	BTN_CLICKED,
}	t_btn_state;

typedef enum e_ui_action
{
	UI_ACTION_NONE,
	UI_ACTION_PLAY,
	UI_ACTION_STEP,
	UI_ACTION_CLEAR,
	UI_ACTION_OPEN_SAVE,
	UI_ACTION_OPEN_LOAD,
	UI_ACTION_RANDOM,
	UI_ACTION_MENU,
	UI_ACTION_CENTER,
	UI_ACTION_TOGGLE_GRID,
	UI_ACTION_TOGGLE_HUD,
	UI_ACTION_TOGGLE_CHUNK_DEBUG,
	UI_ACTION_NEXT_THEME,
	UI_ACTION_UNDO,
	UI_ACTION_COPY_ZONE,
	UI_ACTION_CLEAR_ZONE,
	UI_ACTION_PASTE,
}	t_ui_action;

typedef struct s_hud_info
{
	int				generation;
	bool			running;
	float			speed;
	int				alive_count;
	int				gx;
	int				gy;
	const int		*pop_history;
	int				pop_count;
	int				pop_max;
}	t_hud_info;

typedef enum e_menu_action
{
	MENU_NONE,
	MENU_RESUME,
	MENU_KEYBINDS,
	MENU_CREDITS,
	MENU_QUIT,
}	t_menu_action;

typedef struct s_save_zone_state
{
	int		phase;
	int		x0;
	int		y0;
	int		x1;
	int		y1;
	bool	dragging;
	bool	confirmed;
	bool	cancelled;
	char	name_buf[64];
}	t_save_zone_state;

typedef struct s_place_state
{
	int		rotation;
	int		offset_x;
	int		offset_y;
	bool	confirmed;
	bool	cancelled;
}	t_place_state;

typedef struct s_random_state
{
	int		phase;
	int		x0;
	int		y0;
	int		x1;
	int		y1;
	bool	dragging;
	float	density;
	bool	confirmed;
	bool	cancelled;
}	t_random_state;

typedef struct s_menu_item
{
	const char		*l;
	t_menu_action	a;
}	t_menu_item;

typedef struct s_credit_line
{
	const char		*l;
	const char		*v;
	Color			c;
}	t_credit_line;

typedef struct s_kb_entry
{
	const char		*label;
	const char		*label_cat;
	int				offset;
}	t_kb_entry;

typedef void (*t_icon_draw)(
	float cx,
	float cy,
	float r,
	Color c
);

typedef struct s_search_state
{
	char	*search;
	bool	*search_edit;
	int		*scroll;
}	t_search_state;

typedef struct s_list_ctx
{
	char		(*names)[128];
	int			*filtered;
	int			fcount;
	Rectangle	p;
	int			list_top;
	int			list_bot;
	int			*scroll;
	int			*hovered_idx;
	char		*out_path;
	int			path_len;
}	t_list_ctx;

typedef struct s_toolbar_geom
{
	int	pad;
	int	bsz;
}	t_toolbar_geom;

typedef struct s_list_geom
{
	int		rh;
	int		vis;
	int		lx;
	int		sb_x;
	int		list_w;
	float	track_h;
	bool	sb_dragging;
	float	sb_drag_y;
	int		sb_drag_scroll;
}	t_list_geom;

typedef struct s_browser_view
{
	Rectangle	p;
	int			pw;
	int			ph;
	int			list_top;
	int			list_bot;
}	t_browser_view;

typedef struct s_kb_view
{
	int	list_x;
	int	list_w;
	int	list_top;
	int	list_bot;
}	t_kb_view;

typedef struct s_kb_row
{
	int	cy;
	int	i;
	int	wait_idx;
}	t_kb_row;

// ui_browser-1.c
void			browser_load_files(char names[MAX_RLE][128], int *count);
int				browser_filter(char names[MAX_RLE][128], int count,
					int *filtered, const char *search);

// ui_browser-1b.c
void			draw_rle_preview_cells(t_chunk_map *map, Rectangle dest,
					t_bbox box);
void			draw_rle_preview(const char *path, Rectangle dest);

// ui_browser-2.c
void			draw_list_scrollbar_thumb(t_list_geom g, t_list_ctx ctx,
					Rectangle thumb);
Rectangle		handle_scrollbar_drag(t_list_geom *g, t_list_ctx ctx);

// ui_browser-2b.c
void			draw_list_row_label(t_list_ctx ctx, int ri, Rectangle row,
					bool hov);
bool			draw_list_rows(t_list_ctx ctx, t_list_geom g);
bool			browser_draw_list(t_list_ctx ctx);

// ui_browser-3.c
void			browser_draw_search(Rectangle p, int pw, t_search_state st);

// ui_browser-4.c
void			draw_no_results(t_browser_view v, int fcount, int count);
void			reset_browser_state(int *count, int *scroll, char *search,
					bool *search_edit);
void			draw_browser_header(t_browser_view v);
t_browser_view	browser_layout(void);

// ui_browser-4b.c
void			browser_draw_preview(t_browser_view v,
					char names[MAX_RLE][128], int hovered_idx);
bool			ui_draw_load_browser(char *out_path, int path_len);

// ui_hud.c
void			hud_graph_loop(const int *pop, int start, int n, int gx2,
					int gy2, int gh, float bar_w, int pm);
void			hud_draw_graph(int x, int by, int bh, const int *pop_history,
					int pop_count, int pop_max);
void			hud_draw_status(bool running, int x, int y);
void			hud_draw_text(int generation, float speed, int alive_count,
					int gx, int gy, int by);
void			ui_draw_hud(int generation, bool running, float speed,
					int alive_count, int gx, int gy, const int *pop_history,
					int pop_count, int pop_max);
void			ui_draw_message(const char *msg, float timer);

// ui_icons-1.c
float			icon_get_radius(Rectangle rect);
Color			icon_get_color(bool hov, bool active);
Color			icon_get_border(bool hov, bool active);
t_btn_state		icon_button(Rectangle rect, t_icon_draw draw_fn,
					const char *tooltip, bool active);

// ui_icons-2.c
void			icon_save(float cx, float cy, float r, Color c);
void			icon_load(float cx, float cy, float r, Color c);
void			icon_random(float cx, float cy, float r, Color c);
void			icon_menu(float cx, float cy, float r, Color c);
void			icon_grid(float cx, float cy, float r, Color c);

// ui_icons-3.c
void			icon_hud(float cx, float cy, float r, Color c);
void			icon_chunk_debug(float cx, float cy, float r, Color c);
void			icon_undo(float cx, float cy, float r, Color c);
void			icon_copy(float cx, float cy, float r, Color c);
void			icon_clear_zone(float cx, float cy, float r, Color c);

// ui_icons-4.c
void			icon_play(float cx, float cy, float r, Color c);
void			icon_pause(float cx, float cy, float r, Color c);
void			icon_step(float cx, float cy, float r, Color c);
void			icon_clear(float cx, float cy, float r, Color c);

// ui_icons-5.c
void			icon_paste(float cx, float cy, float r, Color c);

// ui_keybinds-1.c
int				*kb_field(t_key_config *cfg, int offset);
const char		*kname_mod(int k);
const char		*kname_arrow(int k);
const char		*kname_fn(int k, char *buf);
const char		*kname(int k);
extern const	t_kb_entry    g_kb_table[];

// ui_keybinds-2.c
void			kb_draw_sep(t_kb_view v, int cy, const t_kb_entry *e,
					int rh_sep);
void			kb_draw_key_badge(t_kb_view v, t_kb_row r,
					t_key_config *cfg, int rh_key);
void			kb_draw_row(t_kb_view v, t_kb_row r, t_key_config *cfg);
int				kb_scroll(Rectangle panel, int scroll_px, int total_h,
					int list_h);
int				kb_capture(t_key_config *cfg, int wait_idx);

// ui_keybinds-3.c
void			kb_draw_list(t_kb_view v, int scroll_px, int wait_idx,
					t_key_config *cfg);
void			kb_draw_scrollbar(t_kb_view v, int list_h, int total_h,
					int scroll_px);
int				kb_row_click(t_kb_view v, t_kb_row r, t_key_config *cfg);
int				kb_total_h(void);

// ui_keybinds-3b.c
bool			ui_draw_keybinds(t_key_config *cfg);

// ui_menu-1.c
void			menu_init_items(t_menu_item *items);
void			credits_init(t_credit_line *lines);
void			credits_draw_lines(t_credit_line *lines, int n, Rectangle p,
					int pw);
t_menu_action	menu_draw_panel(t_menu_item *items, Rectangle p, int pw,
					int ph);
t_menu_action	ui_draw_menu(void);

// ui_menu-2.c
bool			ui_draw_credits(void);

// ui_random-1.c
void			rand_swap_coords(t_random_state *rs);
void			rand_phase0(t_random_state *rs, t_camera2d_gol cam);
void			rand_slider_input(t_random_state *rs, Rectangle hit, int slx,
					int slw);
void			rand_draw_slider(t_random_state *rs, Rectangle p, int pw);

// ui_random-2.c
void			rand_phase1_buttons(t_random_state *rs, Rectangle p, int pw,
					int ph);
void			rand_phase1(t_random_state *rs, int sw, int sh);
void			ui_draw_random_overlay(t_random_state *rs, t_camera2d_gol cam);

// ui_savezone-1.c
void			sz_phase0_input(t_save_zone_state *sz, t_camera2d_gol cam);
void			sz_draw_empty(void);
void			sz_draw_dragging(t_save_zone_state *sz, t_camera2d_gol cam);
void			sz_phase0_draw(t_save_zone_state *sz, t_camera2d_gol cam);

// ui_savezone-2.c
void			sz_draw_info(t_save_zone_state *sz, Rectangle p, int pw);
void			sz_draw_namefield(t_save_zone_state *sz, Rectangle p, int pw,
					bool *editing);
bool			sz_phase1(t_save_zone_state *sz, int sw, int sh,
					char *out_path, int path_len);
bool			ui_draw_save_zone(t_save_zone_state *sz, t_camera2d_gol cam,
					char *out_path, int path_len);

// ui_savezone-3.c
int				is_valid_name_char(int k);
void			sz_name_edit(t_save_zone_state *sz);

// ui_toolbar-1.c
t_ui_action		toolbar_sim(int *x, int pad, int bsz, bool running);
t_ui_action		toolbar_files(int *x, int pad, int bsz);
t_ui_action		toolbar_tools(int *x, int pad, int bsz);
t_ui_action		toolbar_center_btn(int *x, int pad, int bsz);

// ui_toolbar-2.c
void			toolbar_speed(int *x, int pad, int bsz, float *speed);
t_ui_action		toolbar_view_theme(int *x, t_toolbar_geom g, int theme_idx,
					t_ui_action act);
t_ui_action		toolbar_view(int *x, int pad, int bsz, int theme_idx);
t_ui_action		ui_draw_toolbar(bool running, float *speed, int theme_idx);

// ui.c
void			panel_draw(Rectangle r, Color bg, Color border);
void			text_c(const char *t, int fs, Vector2 pos, Color c);
void			overlay(void);
void			draw_tooltip(Rectangle rect, const char *tooltip);

// ui-2.c
t_btn_state		ui_button(Rectangle r, const char *label, bool active);

#endif
