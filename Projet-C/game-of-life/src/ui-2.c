/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui-2.c                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:38:43 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 08:38:59 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

Color	button_bg(bool hov, bool active)
{
	if (active)
		return (ui_c_active());
	if (hov && IsMouseButtonDown(0))
		return (ui_c_active());
	if (hov)
		return (ui_c_hover());
	return (ui_c_panel());
}

t_btn_state	ui_button(Rectangle r, const char *label, bool active)
{
	Vector2	m;
	bool	hov;
	bool	click;

	m = GetMousePosition();
	hov = CheckCollisionPointRec(m, r);
	click = hov && IsMouseButtonReleased(MOUSE_BUTTON_LEFT);
	DrawRectangleRec(r, button_bg(hov, active));
	if (hov || active)
		DrawRectangleLinesEx(r, 1.0f, ui_c_hi());
	else
		DrawRectangleLinesEx(r, 1.0f, ui_c_border());
	if (hov || active)
		text_c(label, FS, (Vector2){r.x + r.width / 2,
			r.y + r.height / 2}, ui_c_hi());
	else
		text_c(label, FS, (Vector2){r.x + r.width / 2,
			r.y + r.height / 2}, ui_c_text());
	if (click)
		return (BTN_CLICKED);
	if (hov)
		return (BTN_HOVERED);
	return (BTN_IDLE);
}
