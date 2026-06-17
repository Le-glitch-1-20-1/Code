/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_keybinds2.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:38:18 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/17 07:38:21 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"
#include "ui_shared.h"
#include "config.h"
#include <stddef.h>
#include <string.h>

int		*kb_field(t_key_config *cfg, int offset);
const char		*kname(int k);

# define KB_N	28

extern const t_kb_entry	g_kb_table[];

void	kb_draw_sep(int list_x, int list_w, int cy,
	const t_kb_entry *e, int rh_sep)
{
	int	sy;

	sy = cy + 4;
	DrawRectangle(list_x, sy, list_w, rh_sep - 6, (Color){35, 35, 55, 255});
	DrawRectangleLinesEx((Rectangle){(float)list_x, (float)sy,
		(float)list_w, (float)(rh_sep - 6)}, 1.0f, C_BORDER);
	DrawRectangle(list_x, sy, 3, rh_sep - 6, C_HI);
	DrawText(e->label_cat, list_x + 10,
		sy + (rh_sep - 6 - FS) / 2, FS, C_HI);
}

void	kb_draw_key_badge(int list_x, int list_w, int cy,
	int i, int wait_idx, t_key_config *cfg, int rh_key)
{
	const char	*kn;
	int			kw;
	Rectangle	kb;

	if (wait_idx == i)
		kn = "[ ... ]";
	else
		kn = kname(*kb_field(cfg, g_kb_table[i].offset));
	kw = MeasureText(kn, FS) + 16;
	kb = (Rectangle){(float)(list_x + list_w - kw - 6), (float)(cy + 4),
		(float)kw, (float)(rh_key - 10)};
	if (wait_idx == i)
		DrawRectangleRec(kb, C_HI);
	else
		DrawRectangleRec(kb, C_HOVER);
	DrawRectangleLinesEx(kb, 1.0f, C_HI);
	if (wait_idx == i)
		text_c(kn, FS, kb.x + kb.width / 2, kb.y + kb.height / 2, C_BG);
	else
		text_c(kn, FS, kb.x + kb.width / 2, kb.y + kb.height / 2, C_HI);
}

void	kb_draw_row(int list_x, int list_w, int cy, int i,
	int wait_idx, t_key_config *cfg)
{
	const t_kb_entry	*e;
	bool				iw;
	Rectangle			row;
	int					rh_key;

	rh_key = 30;
	e = &g_kb_table[i];
	iw = (wait_idx == i);
	row = (Rectangle){(float)list_x, (float)cy,
		(float)list_w, (float)(rh_key - 2)};
	if (iw)
		DrawRectangleRec(row, C_ACTIVE);
	else
		DrawRectangleRec(row, (Color){22, 22, 36, 200});
	if (iw)
		DrawRectangleLinesEx(row, 1.0f, C_HI);
	else
		DrawRectangleLinesEx(row, 1.0f, (Color){40, 40, 60, 255});
	if (iw)
		DrawText(e->label, list_x + 12, cy + (rh_key - 2 - FS) / 2, FS, C_HI);
	else
		DrawText(e->label, list_x + 12, cy + (rh_key - 2 - FS) / 2, FS, C_TEXT);
	kb_draw_key_badge(list_x, list_w, cy, i, wait_idx, cfg, rh_key);
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
