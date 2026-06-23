/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui.h                                               :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:01:58 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 07:29:17 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef UI_H
# define UI_H

# include "config.h"
# include "renderer.h"
# include "chunk_map.h"

# include "main.h"

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

t_btn_state		ui_button(Rectangle r, const char *label, bool active);
t_ui_action		ui_draw_toolbar(bool running, float *speed, int theme_idx);
t_ui_action		toolbar_center_btn(int *x, int pad, int bsz);
t_ui_action		toolbar_sim(int *x, int pad, int bsz, bool running);
t_ui_action		toolbar_files(int *x, int pad, int bsz);
t_ui_action		toolbar_tools(int *x, int pad, int bsz);
t_menu_action	ui_draw_menu(void);

void			ui_draw_hud(int generation, bool running, float speed,
					int alive_count, int gx, int gy,
					const int *pop_history, int pop_count, int pop_max);
void			sz_name_edit(t_save_zone_state *sz);
void			ui_draw_random_overlay(t_random_state *rs, t_camera2d_gol cam);
void			ui_draw_message(const char *msg, float timer);
void			credits_init(t_credit_line *lines);
void			credits_draw_lines(t_credit_line *lines, int n,
					Rectangle p, int pw);
void			kb_draw_sep(int list_x, int list_w, int cy,
					const t_kb_entry *e, int rh_sep);
void			kb_draw_row(int list_x, int list_w, int cy, int i,
					int wait_idx, t_key_config *cfg);
void			sz_phase0_input(t_save_zone_state *sz, t_camera2d_gol cam);
void			sz_phase0_draw(t_save_zone_state *sz, t_camera2d_gol cam);
void			sz_draw_empty(void);
void			sz_draw_dragging(t_save_zone_state *sz, t_camera2d_gol cam);
bool			ui_draw_keybinds(t_key_config *cfg);
bool			ui_draw_credits(void);
bool			ui_draw_save_zone(t_save_zone_state *sz, t_camera2d_gol cam,
					char *out_path, int path_len);
bool			ui_draw_load_browser(char *out_path, int path_len);
int				*kb_field(t_key_config *cfg, int offset);
int				kb_scroll(Rectangle panel, int scroll_px,
					int total_h, int list_h);
int				kb_capture(t_key_config *cfg, int wait_idx);
const char		*kname(int k);
const char		*kname_mod(int k);
const char		*kname_arrow(int k);
const char		*kname_fn(int k, char *buf);

#endif
