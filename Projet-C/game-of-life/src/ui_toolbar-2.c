/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_toolbar-2.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:04:52 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:20:07 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"
#include "ui_shared.h"
#include "ui_icons.h"
#include "renderer.h"

t_ui_action	toolbar_sim(int *x, int pad, int bsz, bool running);
t_ui_action	toolbar_files(int *x, int pad, int bsz);
t_ui_action	toolbar_tools(int *x, int pad, int bsz);

static t_ui_action	toolbar_view_theme(int *x, int pad, int bsz,
	int theme_idx, t_ui_action act)
{
	t_color_theme	ti;
	Rectangle		tr;
	Vector2			tm2;
	bool			thov;
	bool			tclk;
	char			tt[48];

	if (theme_idx >= 0 && theme_idx < 5)
		ti = get_theme(theme_idx);
	else
		ti = get_theme(0);
	tr = (Rectangle){(float)*x, (float)pad, (float)bsz, (float)bsz};
	tm2 = GetMousePosition();
	thov = CheckCollisionPointRec(tm2, tr);
	tclk = thov && IsMouseButtonReleased(MOUSE_BUTTON_LEFT);
	if (thov)
		DrawRectangleRec(tr, C_HOVER);
	else
		DrawRectangleRec(tr, C_PANEL);
	if (thov)
		DrawRectangleLinesEx(tr, 1.0f, C_HI);
	else
		DrawRectangleLinesEx(tr, 1.0f, C_BORDER);
	DrawCircle((int)(tr.x + tr.width / 2), (int)(tr.y + tr.height / 2),
		tr.width * 0.3f, ti.cell);
	if (thov)
		DrawCircleLines((int)(tr.x + tr.width / 2),
			(int)(tr.y + tr.height / 2), tr.width * 0.3f, C_HI);
	else
		DrawCircleLines((int)(tr.x + tr.width / 2),
			(int)(tr.y + tr.height / 2), tr.width * 0.3f, C_BORDER);
	if (thov)
	{
		snprintf(tt, sizeof(tt), "Theme: %s", ti.name);
		draw_tooltip(tr, tt);
	}
	*x += bsz + pad;
	if (act == UI_ACTION_NONE && tclk)
		return (UI_ACTION_NEXT_THEME);
	return (act);
}

static t_ui_action	toolbar_view(int *x, int pad, int bsz, int theme_idx)
{
	t_ui_action	act;
	int			rx;

	act = toolbar_center_btn(x, pad, bsz);
	DrawLine(*x + 3, pad + 2, *x + 3, pad + bsz - 2, C_BORDER);
	*x += 12;
	rx = *x;
	if (act == UI_ACTION_NONE && icon_button((Rectangle){rx, pad, bsz, bsz},
		icon_grid, "Grille", false) == BTN_CLICKED)
		act = UI_ACTION_TOGGLE_GRID;
	*x += bsz + pad;
	rx = *x;
	if (act == UI_ACTION_NONE && icon_button((Rectangle){rx, pad, bsz, bsz},
		icon_hud, "HUD", false) == BTN_CLICKED)
		act = UI_ACTION_TOGGLE_HUD;
	*x += bsz + pad;
	rx = *x;
	if (act == UI_ACTION_NONE && icon_button((Rectangle){rx, pad, bsz, bsz},
		icon_chunk_debug, "Debug chunks", false) == BTN_CLICKED)
		act = UI_ACTION_TOGGLE_CHUNK_DEBUG;
	*x += bsz + pad;
	act = toolbar_view_theme(x, pad, bsz, theme_idx, act);
	return (act);
}

static void	toolbar_speed(int *x, int pad, int bsz, float *speed)
{
	int			sw2;
	int			ty;
	int			pos;
	float		t;
	float		nt;
	Rectangle	hit;
	Vector2		mm;
	char		buf[8];

	DrawText("SPD", *x, pad + (bsz - FS) / 2, FS, C_DIM);
	*x += MeasureText("SPD", FS) + 6;
	sw2 = 110;
	ty = pad + bsz / 2 - 2;
	DrawRectangle(*x, ty, sw2, 4, C_BORDER);
	t = (*speed - 1.0f) / 119.0f;
	pos = (int)(sw2 * t);
	DrawRectangle(*x, ty, pos, 4, C_HI);
	DrawCircle(*x + pos, ty + 2, 5, C_HI);
	hit = (Rectangle){(float)(*x - 6), pad, (float)(sw2 + 12), bsz};
	mm = GetMousePosition();
	if (CheckCollisionPointRec(mm, hit) && IsMouseButtonDown(0))
	{
		nt = (mm.x - *x) / sw2;
		if (nt < 0)
			nt = 0;
		if (nt > 1)
			nt = 1;
		*speed = 1.0f + nt * 119.0f;
	}
	snprintf(buf, sizeof(buf), "%.0f", *speed);
	DrawText(buf, *x + sw2 + 6, pad + (bsz - FS) / 2, FS, C_HI);
	*x += sw2 + 28;
}

t_ui_action	ui_draw_toolbar(bool running, float *speed, int theme_idx)
{
	int			sw;
	int			bh;
	int			pad;
	int			bsz;
	int			x;
	int			rx;
	t_ui_action	act;

	sw = GetScreenWidth();
	bh = 40;
	pad = 5;
	bsz = bh - pad * 2;
	act = UI_ACTION_NONE;
	DrawRectangle(0, 0, sw, bh, C_PANEL);
	DrawLine(0, bh, sw, bh, C_BORDER);
	x = pad + 8;
	act = toolbar_sim(&x, pad, bsz, running);
	if (act == UI_ACTION_NONE)
		act = toolbar_files(&x, pad, bsz);
	if (act == UI_ACTION_NONE)
		act = toolbar_tools(&x, pad, bsz);
	DrawLine(x + 3, pad + 2, x + 3, pad + bsz - 2, C_BORDER);
	x += 12;
	if (act == UI_ACTION_NONE)
		act = toolbar_view(&x, pad, bsz, theme_idx);
	DrawLine(x + 3, pad + 2, x + 3, pad + bsz - 2, C_BORDER);
	x += 12;
	toolbar_speed(&x, pad, bsz, speed);
	rx = sw - bsz - pad - 8;
	if (act == UI_ACTION_NONE && icon_button((Rectangle){rx, pad, bsz, bsz},
		icon_menu, "Menu", false) == BTN_CLICKED)
		act = UI_ACTION_MENU;
	return (act);
}
