/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_keybinds-3.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:04:34 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 23:05:57 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

int	kb_row_click(t_kb_view v, t_kb_row r, t_key_config *cfg)
{
	const char	*kn;
	int			kw;
	Rectangle	hit;

	if (r.wait_idx == r.i)
		return (r.wait_idx);
	kn = kname(*kb_field(cfg, g_kb_table[r.i].offset));
	kw = MeasureText(kn, FS) + 16;
	hit = (Rectangle){
		(float)(v.list_x + v.list_w - kw - 6),
		(float)(r.cy + 4),
		(float)kw,
		(float)(30 - 10)
	};
	if (CheckCollisionPointRec(GetMousePosition(), hit)
		&& IsMouseButtonReleased(0))
		return (r.i);
	return (r.wait_idx);
}

void	kb_draw_list(t_kb_view v, int scroll_px, int wait_idx,
			t_key_config *cfg)
{
	int	cy;
	int	i;
	int	rh_key;
	int	rh_sep;

	rh_key = 30;
	rh_sep = 28;
	cy = v.list_top - scroll_px;
	i = 0;
	while (i < KB_N)
	{
		if (!g_kb_table[i].label)
		{
			if (cy + rh_sep > v.list_top && cy < v.list_bot)
				kb_draw_sep(v, cy, &g_kb_table[i], rh_sep);
			cy += rh_sep;
		}
		else
		{
			if (cy + rh_key > v.list_top && cy < v.list_bot)
			{
				kb_draw_row(v, (t_kb_row){cy, i, wait_idx}, cfg);
				wait_idx = kb_row_click(v, (t_kb_row){cy, i, wait_idx}, cfg);
			}
			cy += rh_key;
		}
		i++;
	}
}

void	kb_draw_scrollbar(t_kb_view v, int list_h, int total_h, int scroll_px)
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
	bar_y = v.list_top + (list_h - bar_h) * scroll_px / ms;
	DrawRectangle(v.list_x + v.list_w + 2, v.list_top, 4, list_h,
		(Color){30, 30, 48, 200});
	DrawRectangle(v.list_x + v.list_w + 2, (int)bar_y, 4, (int)bar_h,
		C_BORDER);
}

int	kb_total_h(void)
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
	t_kb_view	v;
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
	v.list_x = (int)p.x + 14;
	v.list_top = (int)p.y + 50;
	v.list_bot = (int)p.y + ph - 48;
	v.list_w = pw - 28;
	scroll_px = kb_scroll(p, scroll_px, kb_total_h(), v.list_bot - v.list_top);
	if (wait_idx >= 0)
		wait_idx = kb_capture(cfg, wait_idx);
	BeginScissorMode(v.list_x, v.list_top, v.list_w, v.list_bot - v.list_top);
	kb_draw_list(v, scroll_px, wait_idx, cfg);
	EndScissorMode();
	kb_draw_scrollbar(v, v.list_bot - v.list_top, kb_total_h(), scroll_px);
	if (ui_button((Rectangle){p.x + pw / 2.0f - 65, p.y + ph - 40, 130, 32},
		"Retour", false) == BTN_CLICKED || IsKeyPressed(KEY_ESCAPE))
	{
		wait_idx = -1;
		scroll_px = 0;
		return (true);
	}
	return (false);
}
