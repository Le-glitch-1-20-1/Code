/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui.c                                               :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:38:43 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:20:08 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"
#include "renderer.h"
#include "save.h"
#include "config.h"
#include <stdio.h>
#include <string.h>
#include <stddef.h>
#include <math.h>
#include <stdlib.h>
#include <ctype.h>

#define C_BG		(Color){14,  14,  18,  255}
#define C_PANEL		(Color){24,  24,  34,  245}
#define C_PANEL2	(Color){30,  30,  44,  255}
#define C_BORDER	(Color){55,  55,  80,  255}
#define C_HI		(Color){127, 119, 221, 255}
#define C_TEXT		(Color){210, 210, 225, 255}
#define C_DIM		(Color){100, 100, 125, 255}
#define C_HOVER		(Color){42,  40,  68,  255}
#define C_ACTIVE	(Color){72,  66,  148, 255}
#define C_GREEN		(Color){72,  200, 120, 255}
#define C_YELLOW	(Color){230, 185, 55,  255}
#define C_RED		(Color){210, 72,  72,  255}
#define C_OVERLAY	(Color){0,   0,   0,   195}
#define C_ACCENT2	(Color){80,  195, 145, 255}
#define C_ORANGE	(Color){220, 140, 50,  255}

#define FS		15
#define FM		18
#define FL		24
#define FXL		32

void	panel_draw(Rectangle r, Color bg, Color border)
{
	DrawRectangleRec(r, bg);
	DrawRectangleLinesEx(r, 1.0f, border);
}

void	text_c(const char *t, int fs, float cx, float cy, Color c)
{
	DrawText(t, (int)(cx - MeasureText(t, fs) / 2),
		(int)(cy - fs / 2), fs, c);
}

void	overlay(void)
{
	DrawRectangle(0, 0, GetScreenWidth(), GetScreenHeight(), C_OVERLAY);
}

void	draw_tooltip(Rectangle rect, const char *tooltip)
{
	int	tw;
	int	tx;
	int	ty;

	tw = MeasureText(tooltip, FS - 2) + 10;
	tx = (int)rect.x + (int)rect.width / 2 - tw / 2;
	ty = (int)rect.y + (int)rect.height + 4;
	DrawRectangle(tx - 2, ty - 2, tw + 4, FS + 4, C_PANEL);
	DrawRectangleLinesEx((Rectangle){tx - 2, ty - 2, tw + 4, FS + 4},
		1, C_BORDER);
	DrawText(tooltip, tx + 3, ty + 1, FS - 2, C_DIM);
}

t_btn_state	ui_button(Rectangle r, const char *label, bool active)
{
	Vector2	m;
	bool	hov;
	bool	click;
	Color	bg;

	m = GetMousePosition();
	hov = CheckCollisionPointRec(m, r);
	click = hov && IsMouseButtonReleased(MOUSE_BUTTON_LEFT);
	if (active)
		bg = C_ACTIVE;
	else if (hov && IsMouseButtonDown(0))
		bg = C_ACTIVE;
	else if (hov)
		bg = C_HOVER;
	else
		bg = C_PANEL;
	DrawRectangleRec(r, bg);
	if (hov || active)
		DrawRectangleLinesEx(r, 1.0f, C_HI);
	else
		DrawRectangleLinesEx(r, 1.0f, C_BORDER);
	if (hov || active)
		text_c(label, FS, r.x + r.width / 2, r.y + r.height / 2, C_HI);
	else
		text_c(label, FS, r.x + r.width / 2, r.y + r.height / 2, C_TEXT);
	if (click)
		return (BTN_CLICKED);
	if (hov)
		return (BTN_HOVERED);
	return (BTN_IDLE);
}
