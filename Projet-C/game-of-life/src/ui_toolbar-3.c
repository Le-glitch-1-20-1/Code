/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_toolbar-3.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/27 21:05:20 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 21:05:20 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

static t_ui_action	toolbar_tools_btns(int *x, int pad, int bsz)
{
	t_ui_action		act;
	t_toolbar_geom	g;

	g = (t_toolbar_geom){pad, bsz};
	act = UI_ACTION_NONE;
	if (toolbar_btn(x, g, icon_copy, "Copier zone"))
		act = UI_ACTION_COPY_ZONE;
	if (act == UI_ACTION_NONE && toolbar_btn(x, g, icon_paste, "Coller"))
		act = UI_ACTION_PASTE;
	if (act == UI_ACTION_NONE && toolbar_btn(x, g, icon_clear_zone,
			"Effacer zone"))
		act = UI_ACTION_CLEAR_ZONE;
	return (act);
}

t_ui_action	toolbar_tools(int *x, int pad, int bsz)
{
	t_ui_action		act;
	t_toolbar_geom	g;

	g = (t_toolbar_geom){pad, bsz};
	act = UI_ACTION_NONE;
	DrawLine(*x + 3, pad + 2, *x + 3, pad + bsz - 2, ui_c_border());
	*x += 12;
	if (toolbar_btn(x, g, icon_random, "Aleatoire"))
		act = UI_ACTION_RANDOM;
	if (act == UI_ACTION_NONE)
		act = toolbar_tools_btns(x, pad, bsz);
	return (act);
}

static void	toolbar_center_crosshair(Rectangle rb, bool hov2)
{
	float	r2;
	float	cx2;
	float	cy2;
	Color	col;

	r2 = rb.width * 0.35f * 0.8f;
	cx2 = rb.x + rb.width / 2;
	cy2 = rb.y + rb.height / 2;
	if (hov2)
		col = ui_c_hi();
	else
		col = ui_c_text();
	DrawLineEx((Vector2){cx2 - r2, cy2}, (Vector2){cx2 + r2, cy2}, 1.5f, col);
	DrawLineEx((Vector2){cx2, cy2 - r2}, (Vector2){cx2, cy2 + r2}, 1.5f, col);
	DrawCircleLines((int)cx2, (int)cy2, (int)(r2 * 0.6f), col);
	if (hov2)
		draw_tooltip(rb, "Recentrer");
}

t_ui_action	toolbar_center_btn(int *x, int pad, int bsz)
{
	Rectangle	rb;
	Vector2		m2;
	bool		hov2;
	bool		click2;

	rb = (Rectangle){(float)*x, (float)pad, (float)bsz, (float)bsz};
	m2 = GetMousePosition();
	hov2 = CheckCollisionPointRec(m2, rb);
	click2 = hov2 && IsMouseButtonReleased(MOUSE_BUTTON_LEFT);
	if (hov2 && IsMouseButtonDown(0))
		DrawRectangleRec(rb, ui_c_active());
	else if (hov2)
		DrawRectangleRec(rb, ui_c_hover());
	else
		DrawRectangleRec(rb, ui_c_panel());
	if (hov2)
		DrawRectangleLinesEx(rb, 1.0f, ui_c_hi());
	else
		DrawRectangleLinesEx(rb, 1.0f, ui_c_border());
	toolbar_center_crosshair(rb, hov2);
	*x += bsz + pad;
	if (click2)
		return (UI_ACTION_CENTER);
	return (UI_ACTION_NONE);
}
