/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/* ui_keybinds3.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/* By: student <student@student.42.fr>              +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/* Created: 2025/01/01 00:00:00 by student           #+#    #+#             */
/* Updated: 2025/01/01 00:00:00 by student          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"
#include "ui_shared.h"
#include "config.h"
#include <stddef.h>
#include <string.h>

int	*kb_field(t_key_config *cfg, int offset);
const char	*kname(int k);
void	kb_draw_sep(int list_x, int list_w, int cy, const t_kb_entry *e, int rh_sep);
void	kb_draw_row(int list_x, int list_w, int cy, int i, int wait_idx, t_key_config *cfg);
int	kb_scroll(Rectangle panel, int scroll_px, int total_h, int list_h);
int	kb_capture(t_key_config *cfg, int wait_idx);


# define KB_N	28
extern const t_kb_entry	g_kb_table[];

static int	kb_row_click(int list_x, int list_w, int cy, int i,
	int wait_idx, t_key_config *cfg)
{
	const char	*kn;
	int			kw;
	Rectangle	hit;

	if (wait_idx == i)
		return (wait_idx);
	kn = kname(*kb_field(cfg, g_kb_table[i].offset));
	kw = MeasureText(kn, FS) + 16;
	hit = (Rectangle){
		(float)(list_x + list_w - kw - 6),
		(float)(cy + 4),
		(float)kw,
		(float)(30 - 10)
	};
	if (CheckCollisionPointRec(GetMousePosition(), hit)
		&& IsMouseButtonReleased(0))
		return (i);
	return (wait_idx);
}

static void	kb_draw_list(int list_x, int list_w, int list_top,
	int list_bot, int scroll_px, int wait_idx, t_key_config *cfg)
{
	int	cy;
	int	i;
	int	rh_key;
	int	rh_sep;

	rh_key = 30;
	rh_sep = 28;
	cy = list_top - scroll_px;
	i = 0;
	while (i < KB_N)
	{
		if (!g_kb_table[i].label)
		{
			if (cy + rh_sep > list_top && cy < list_bot)
				kb_draw_sep(list_x, list_w, cy, &g_kb_table[i], rh_sep);
			cy += rh_sep;
		}
		else
		{
			if (cy + rh_key > list_top && cy < list_bot)
			{
				kb_draw_row(list_x, list_w, cy, i, wait_idx, cfg);
				wait_idx = kb_row_click(list_x, list_w, cy, i, wait_idx, cfg);
			}
			cy += rh_key;
		}
		i++;
	}
}

static void	kb_draw_scrollbar(int list_x, int list_w, int list_top,
	int list_h, int total_h, int scroll_px)
{
	float	ratio;
	float	bar_h;
	int		ms;
	float	bar_y;

	if (total_h <= list_h)
		return ;
	ratio = (float)list_h / total_h;
	bar_h = list_h * ratio;
	ms = total_h - list_h;
	bar_y = list_top + (list_h - bar_h) * scroll_px / ms;
	DrawRectangle(list_x + list_w + 2, list_top, 4, list_h,
		(Color){30, 30, 48, 200});
	DrawRectangle(list_x + list_w + 2, (int)bar_y, 4, (int)bar_h, C_BORDER);
}

static int	kb_total_h(void)
{
	int	total_h;
	int	k;

	total_h = 0;
	k = 0;
	while (k < KB_N)
	{
		if (g_kb_table[k].label)
			total_h += 30;
		else
			total_h += 28;
		k++;
	}
	return (total_h);
}

bool	ui_draw_keybinds(t_key_config *cfg)
{
	static int	scroll_px = 0;
	static int	wait_idx = -1;
	int			pw;
	int			ph;
	int			list_x;
	int			list_top;
	int			list_bot;
	int			list_h;
	Rectangle	p;

	overlay();
	ph = GetScreenHeight() - 80;
	if (ph > 680)
		ph = 680;
	if (ph < 300)
		ph = 300;
	pw = 560;
	p = (Rectangle){(GetScreenWidth() - pw) / 2.0f,
		(GetScreenHeight() - ph) / 2.0f, (float)pw, (float)ph};
	panel_draw(p, C_PANEL, C_HI);
	text_c("CONFIGURATION DES TOUCHES", FM, p.x + pw / 2.0f, p.y + 22, C_HI);
	DrawLine((int)p.x + 10, (int)p.y + 42,
		(int)p.x + pw - 10, (int)p.y + 42, C_BORDER);
	list_x = (int)p.x + 14;
	list_top = (int)p.y + 50;
	list_bot = (int)p.y + ph - 48;
	list_h = list_bot - list_top;
	scroll_px = kb_scroll(p, scroll_px, kb_total_h(), list_h);
	if (wait_idx >= 0)
		wait_idx = kb_capture(cfg, wait_idx);
	BeginScissorMode(list_x, list_top, pw - 28, list_h);
	kb_draw_list(list_x, pw - 28, list_top, list_bot, scroll_px,
		wait_idx, cfg);
	EndScissorMode();
	kb_draw_scrollbar(list_x, pw - 28, list_top, list_h, kb_total_h(), scroll_px);
	if (ui_button(
		(Rectangle){p.x + pw / 2.0f - 65, p.y + ph - 40, 130, 32},
		"Retour", false) == BTN_CLICKED || IsKeyPressed(KEY_ESCAPE))
	{
		wait_idx = -1;
		scroll_px = 0;
		return (true);
	}
	return (false);
}
