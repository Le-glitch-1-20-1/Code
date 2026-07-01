/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui.c                                               :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:38:43 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 09:19:02 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

void	panel_draw(Rectangle r, Color bg, Color border)
{
	DrawRectangleRec(r, bg);
	DrawRectangleLinesEx(r, 1.0f, border);
}

void	text_c(const char *t, int fs, Vector2 pos, Color c)
{
	DrawText(t, (int)(pos.x - MeasureText(t, fs) / 2),
		(int)(pos.y - fs / 2), fs, c);
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
