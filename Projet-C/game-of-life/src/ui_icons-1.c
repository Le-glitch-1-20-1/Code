/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_icons-1.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:19:08 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:19:53 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"
#include "ui_shared.h"
#include "ui_icons.h"

static Color	icon_get_color(bool hov, bool active)
{
	if (hov || active)
		return (C_HI);
	return (C_TEXT);
}

static Color	icon_get_border(bool hov, bool active)
{
	if (hov || active)
		return (C_HI);
	return (C_BORDER);
}

static float	icon_get_radius(Rectangle rect)
{
	if (rect.width < rect.height)
		return (rect.width * 0.35f);
	return (rect.height * 0.35f);
}

t_btn_state	icon_button(Rectangle rect, t_icon_draw draw_fn,
	const char *tooltip, bool active)
{
	Vector2	m;
	bool	hov;
	bool	click;
	Color	bg;
	float	r2;

	m = GetMousePosition();
	hov = CheckCollisionPointRec(m, rect);
	click = hov && IsMouseButtonReleased(MOUSE_BUTTON_LEFT);
	if (active)
		bg = C_ACTIVE;
	else if (hov && IsMouseButtonDown(0))
		bg = C_ACTIVE;
	else if (hov)
		bg = C_HOVER;
	else
		bg = C_PANEL;
	DrawRectangleRec(rect, bg);
	DrawRectangleLinesEx(rect, 1.0f, icon_get_border(hov, active));
	r2 = icon_get_radius(rect);
	draw_fn(rect.x + rect.width / 2, rect.y + rect.height / 2, r2,
		icon_get_color(hov, active));
	if (hov && tooltip)
		draw_tooltip(rect, tooltip);
	if (click)
		return (BTN_CLICKED);
	if (hov)
		return (BTN_HOVERED);
	return (BTN_IDLE);
}
