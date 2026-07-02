/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_keybinds-2.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:05:50 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 23:05:50 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

void	kb_draw_sep(t_kb_view v, int cy, const t_kb_entry *e, int rh_sep)
{
	int	sy;

	sy = cy + 4;
	DrawRectangle(v.list_x, sy, v.list_w, rh_sep - 6,
		(Color){35, 35, 55, 255});
	DrawRectangleLinesEx((Rectangle){(float)v.list_x, (float)sy,
		(float)v.list_w, (float)(rh_sep - 6)}, 1.0f, ui_c_border());
	DrawRectangle(v.list_x, sy, 3, rh_sep - 6, ui_c_hi());
	DrawText(e->label_cat, v.list_x + 10,
		sy + (rh_sep - 6 - FS) / 2, FS, ui_c_hi());
}

void	kb_draw_key_badge(t_kb_view v, t_kb_row r, t_key_config *cfg,
			int rh_key)
{
	const char	*kn;
	int			kw;
	Rectangle	kb;

	if (r.wait_idx == r.i)
		kn = "[ ... ]";
	else
		kn = kname(*kb_field(cfg, g_kb_table[r.i].offset));
	kw = MeasureText(kn, FS) + 16;
	kb = (Rectangle){(float)(v.list_x + v.list_w - kw - 6),
		(float)(r.cy + 4), (float)kw, (float)(rh_key - 10)};
	if (r.wait_idx == r.i)
		DrawRectangleRec(kb, ui_c_hi());
	else
		DrawRectangleRec(kb, ui_c_hover());
	DrawRectangleLinesEx(kb, 1.0f, ui_c_hi());
	if (r.wait_idx == r.i)
		text_c(kn, FS, (Vector2){kb.x + kb.width / 2, kb.y + kb.height / 2},
			ui_c_bg());
	else
		text_c(kn, FS, (Vector2){kb.x + kb.width / 2, kb.y + kb.height / 2},
			ui_c_hi());
}

void	kb_draw_row(t_kb_view v, t_kb_row r, t_key_config *cfg)
{
	const t_kb_entry	*e;
	bool				iw;
	Rectangle			row;
	int					rh_key;

	rh_key = 30;
	e = &g_kb_table[r.i];
	iw = (r.wait_idx == r.i);
	row = (Rectangle){(float)v.list_x, (float)r.cy,
		(float)v.list_w, (float)(rh_key - 2)};
	if (iw)
		DrawRectangleRec(row, ui_c_active());
	else
		DrawRectangleRec(row, (Color){22, 22, 36, 200});
	if (iw)
		DrawRectangleLinesEx(row, 1.0f, ui_c_hi());
	else
		DrawRectangleLinesEx(row, 1.0f, (Color){40, 40, 60, 255});
	if (iw)
		DrawText(e->label, v.list_x + 12,
			r.cy + (rh_key - 2 - FS) / 2, FS, ui_c_hi());
	else
		DrawText(e->label, v.list_x + 12,
			r.cy + (rh_key - 2 - FS) / 2, FS, ui_c_text());
	kb_draw_key_badge(v, r, cfg, rh_key);
}

int	kb_scroll(Rectangle panel, int scroll_px, int total_h, int list_h)
{
	int	max_scroll;

	if (CheckCollisionPointRec(GetMousePosition(), panel))
		scroll_px -= (int)(GetMouseWheelMove() * 30);
	max_scroll = total_h - list_h;
	if (max_scroll < 0)
		max_scroll = 0;
	if (scroll_px < 0)
		scroll_px = 0;
	if (scroll_px > max_scroll)
		scroll_px = max_scroll;
	return (scroll_px);
}

int	kb_capture(t_key_config *cfg, int wait_idx)
{
	int	pr;

	pr = GetKeyPressed();
	if (pr > 0 && pr != KEY_ESCAPE)
	{
		*kb_field(cfg, g_kb_table[wait_idx].offset) = pr;
		save_key_config("keys.cfg", cfg);
		return (-1);
	}
	if (IsKeyPressed(KEY_ESCAPE))
		return (-1);
	return (wait_idx);
}
