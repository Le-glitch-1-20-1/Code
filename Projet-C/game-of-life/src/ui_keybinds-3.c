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

static int	kb_draw_list_step(t_kb_view v, t_kb_row r, t_key_config *cfg)
{
	int	rh_key;
	int	rh_sep;

	rh_key = 30;
	rh_sep = 28;
	if (!g_kb_table[r.i].label)
	{
		if (r.cy + rh_sep > v.list_top && r.cy < v.list_bot)
			kb_draw_sep(v, r.cy, &g_kb_table[r.i], rh_sep);
	}
	else if (r.cy + rh_key > v.list_top && r.cy < v.list_bot)
	{
		kb_draw_row(v, r, cfg);
		r.wait_idx = kb_row_click(v, r, cfg);
	}
	return (r.wait_idx);
}

void	kb_draw_list(t_kb_view v, int scroll_px, int wait_idx,
			t_key_config *cfg)
{
	int	cy;
	int	i;

	cy = v.list_top - scroll_px;
	i = 0;
	while (i < KB_N)
	{
		wait_idx = kb_draw_list_step(v, (t_kb_row){cy, i, wait_idx}, cfg);
		if (!g_kb_table[i].label)
			cy += 28;
		else
			cy += 30;
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
		ui_c_border());
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
