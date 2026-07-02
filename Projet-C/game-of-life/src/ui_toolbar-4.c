/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_toolbar-4.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/27 21:05:20 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 21:05:20 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

static void	toolbar_speed_slider(int *x, int pad, int bsz, float *speed)
{
	int			sw2;
	int			ty;
	int			pos;
	float		t;
	Rectangle	hit;

	sw2 = 110;
	ty = pad + bsz / 2 - 2;
	DrawRectangle(*x, ty, sw2, 4, ui_c_border());
	t = (*speed - 1.0f) / 119.0f;
	pos = (int)(sw2 * t);
	DrawRectangle(*x, ty, pos, 4, ui_c_hi());
	DrawCircle(*x + pos, ty + 2, 5, ui_c_hi());
	hit = (Rectangle){(float)(*x - 6), pad, (float)(sw2 + 12), bsz};
	if (CheckCollisionPointRec(GetMousePosition(), hit)
		&& IsMouseButtonDown(0))
	{
		t = (GetMousePosition().x - *x) / sw2;
		if (t < 0)
			t = 0;
		if (t > 1)
			t = 1;
		*speed = 1.0f + t * 119.0f;
	}
	*x += sw2 + 28;
}

void	toolbar_speed(int *x, int pad, int bsz, float *speed)
{
	char	buf[8];

	DrawText("SPD", *x, pad + (bsz - FS) / 2, FS, ui_c_dim());
	*x += MeasureText("SPD", FS) + 6;
	toolbar_speed_slider(x, pad, bsz, speed);
	snprintf(buf, sizeof(buf), "%.0f", *speed);
	DrawText(buf, *x - 22, pad + (bsz - FS) / 2, FS, ui_c_hi());
}

static t_ui_action	toolbar_draw_actions(int *x, int pad, int bsz,
						bool running)
{
	t_ui_action	act;

	act = toolbar_sim(x, pad, bsz, running);
	if (act == UI_ACTION_NONE)
		act = toolbar_files(x, pad, bsz);
	if (act == UI_ACTION_NONE)
		act = toolbar_tools(x, pad, bsz);
	DrawLine(*x + 3, pad + 2, *x + 3, pad + bsz - 2, ui_c_border());
	*x += 12;
	if (act == UI_ACTION_NONE)
		act = toolbar_view(x, pad, bsz, 0);
	DrawLine(*x + 3, pad + 2, *x + 3, pad + bsz - 2, ui_c_border());
	*x += 12;
	return (act);
}

t_ui_action	ui_draw_toolbar(bool running, float *speed, int theme_idx)
{
	int			sw;
	int			pad;
	int			bsz;
	int			x;
	t_ui_action	act;

	sw = GetScreenWidth();
	pad = 5;
	bsz = 40 - pad * 2;
	DrawRectangle(0, 0, sw, 40, ui_c_panel());
	DrawLine(0, 40, sw, 40, ui_c_border());
	x = pad + 8;
	act = toolbar_draw_actions(&x, pad, bsz, running);
	(void)theme_idx;
	toolbar_speed(&x, pad, bsz, speed);
	if (act == UI_ACTION_NONE && icon_button((Rectangle){sw - bsz - pad - 8,
			pad, bsz, bsz}, icon_menu, "Menu", false) == BTN_CLICKED)
		act = UI_ACTION_MENU;
	return (act);
}
