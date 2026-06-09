/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/* ui_random.c                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/* By: student <student@student.42.fr>              +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/* Created: 2025/01/01 00:00:00 by student           #+#    #+#             */
/* Updated: 2025/01/01 00:00:00 by student          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"
#include "ui_shared.h"
#include <math.h>

static void	rand_phase0(t_random_state *rs, t_camera2d_gol cam)
{
	Vector2	m;
	bool	on_ui;
	int		t;

	m = GetMousePosition();
	on_ui = (m.y < 42);
	if (!on_ui && IsMouseButtonPressed(MOUSE_BUTTON_LEFT))
	{
		rs->dragging = true;
		rs->x0 = (int)floorf((m.x - cam.offset.x) / cam.zoom);
		rs->y0 = (int)floorf((m.y - cam.offset.y) / cam.zoom);
		rs->x1 = rs->x0;
		rs->y1 = rs->y0;
	}
	if (rs->dragging && IsMouseButtonDown(MOUSE_BUTTON_LEFT))
	{
		rs->x1 = (int)floorf((m.x - cam.offset.x) / cam.zoom);
		rs->y1 = (int)floorf((m.y - cam.offset.y) / cam.zoom);
	}
	if (rs->dragging && IsMouseButtonReleased(MOUSE_BUTTON_LEFT))
	{
		rs->dragging = false;
		if (rs->x0 > rs->x1)
		{
			t = rs->x0;
			rs->x0 = rs->x1;
			rs->x1 = t;
		}
		if (rs->y0 > rs->y1)
		{
			t = rs->y0;
			rs->y0 = rs->y1;
			rs->y1 = t;
		}
		if (rs->x1 - rs->x0 + 1 > 1 && rs->y1 - rs->y0 + 1 > 1)
			rs->phase = 1;
	}
	if (IsKeyPressed(KEY_ESCAPE))
		rs->cancelled = true;
}

static void	rand_draw_slider(t_random_state *rs, Rectangle p, int pw)
{
	int			slx;
	int			sly;
	int			slw;
	int			pos;
	float		nt;
	char		dpct[16];
	char		preview[48];
	Rectangle	hit;
	Vector2		mm;

	slx = (int)p.x + 90;
	sly = (int)p.y + 88;
	slw = pw - 140;
	DrawRectangle(slx, sly, slw, 4, C_BORDER);
	pos = (int)(rs->density * slw);
	DrawRectangle(slx, sly, pos, 4, C_HI);
	DrawCircle(slx + pos, sly + 2, 6, C_HI);
	hit = (Rectangle){(float)slx, (float)(p.y + 74), (float)slw, 24};
	mm = GetMousePosition();
	if (CheckCollisionPointRec(mm, hit) && IsMouseButtonDown(0))
	{
		nt = (mm.x - slx) / slw;
		if (nt < 0)
			nt = 0;
		if (nt > 1)
			nt = 1;
		rs->density = nt;
	}
	snprintf(dpct, sizeof(dpct), "%.0f%%", rs->density * 100);
	DrawText(dpct, slx + slw + 8, sly - 3, FS, C_HI);
	snprintf(preview, sizeof(preview), "~%d cellules vivantes",
		(int)((rs->x1 - rs->x0 + 1) * (rs->y1 - rs->y0 + 1) * rs->density));
	DrawText(preview, (int)p.x + 20, (int)p.y + 108, FS - 1, C_DIM);
}

static void	rand_phase1(t_random_state *rs, int sw, int sh)
{
	char		info[64];
	Rectangle	p;
	int			pw;
	int			ph;

	pw = 420;
	ph = 220;
	overlay();
	p = (Rectangle){(sw - pw) / 2.0f, (sh - ph) / 2.0f, pw, ph};
	panel_draw(p, C_PANEL, C_HI);
	text_c("REMPLISSAGE ALEATOIRE", FM, p.x + pw / 2, p.y + 26, C_HI);
	DrawLine((int)p.x + 10, (int)p.y + 44,
		(int)p.x + pw - 10, (int)p.y + 44, C_BORDER);
	snprintf(info, sizeof(info), "Region : %d x %d cellules",
		rs->x1 - rs->x0 + 1, rs->y1 - rs->y0 + 1);
	DrawText(info, (int)p.x + 20, (int)p.y + 54, FS, C_TEXT);
	DrawText("Densite :", (int)p.x + 20, (int)p.y + 82, FS, C_DIM);
	rand_draw_slider(rs, p, pw);
	if (ui_button((Rectangle){p.x + 20, p.y + ph - 46, 140, 34},
		"Remplir", false) == BTN_CLICKED)
		rs->confirmed = true;
	if (ui_button(
		(Rectangle){p.x + pw - 160, p.y + ph - 46, 140, 34},
		"Annuler", false) == BTN_CLICKED || IsKeyPressed(KEY_ESCAPE))
		rs->cancelled = true;
}

void	ui_draw_random_overlay(t_random_state *rs, t_camera2d_gol cam)
{
	if (rs->phase == 0)
		rand_phase0(rs, cam);
	else
		rand_phase1(rs, GetScreenWidth(), GetScreenHeight());
}
