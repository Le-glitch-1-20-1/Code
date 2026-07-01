/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_icons-1.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:19:08 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 22:29:31 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

Color	icon_get_color(bool hov, bool active)
{
	if (hov || active)
		return (C_HI);
	return (C_TEXT);
}

Color	icon_get_border(bool hov, bool active)
{
	if (hov || active)
		return (C_HI);
	return (C_BORDER);
}

float	icon_get_radius(Rectangle rect)
{
	if (rect.width < rect.height)
		return (rect.width * 0.35f);
	return (rect.height * 0.35f);
}

static void	icon_btn_draw(Rectangle rect, t_icon_draw draw_fn,
				bool hov, bool active)
{
	Color	bg;

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
	draw_fn(rect.x + rect.width / 2, rect.y + rect.height / 2,
		icon_get_radius(rect), icon_get_color(hov, active));
}

t_btn_state	icon_button(Rectangle rect, t_icon_draw draw_fn,
				const char *tooltip, bool active)
{
	bool	hov;
	bool	click;

	hov = CheckCollisionPointRec(GetMousePosition(), rect);
	click = hov && IsMouseButtonReleased(MOUSE_BUTTON_LEFT);
	icon_btn_draw(rect, draw_fn, hov, active);
	if (hov && tooltip)
		draw_tooltip(rect, tooltip);
	if (click)
		return (BTN_CLICKED);
	if (hov)
		return (BTN_HOVERED);
	return (BTN_IDLE);
}
