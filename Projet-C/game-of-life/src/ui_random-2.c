/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_random-2.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:06:23 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 22:47:01 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

void	rand_phase1_buttons(t_random_state *rs, Rectangle p, int pw, int ph)
{
	if (ui_button((Rectangle){p.x + 20, p.y + ph - 46, 140, 34},
		"Remplir", false) == BTN_CLICKED)
		rs->confirmed = true;
	if (ui_button((Rectangle){p.x + pw - 160, p.y + ph - 46, 140, 34},
		"Annuler", false) == BTN_CLICKED || IsKeyPressed(KEY_ESCAPE))
		rs->cancelled = true;
}

void	rand_phase1(t_random_state *rs, int sw, int sh)
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
	text_c("REMPLISSAGE ALEATOIRE", FM, (Vector2){p.x + pw / 2,
		p.y + 26}, C_HI);
	DrawLine((int)p.x + 10, (int)p.y + 44,
		(int)p.x + pw - 10, (int)p.y + 44, C_BORDER);
	snprintf(info, sizeof(info), "Region : %d x %d cellules",
		rs->x1 - rs->x0 + 1, rs->y1 - rs->y0 + 1);
	DrawText(info, (int)p.x + 20, (int)p.y + 54, FS, C_TEXT);
	DrawText("Densite :", (int)p.x + 20, (int)p.y + 82, FS, C_DIM);
	rand_draw_slider(rs, p, pw);
	rand_phase1_buttons(rs, p, pw, ph);
}

void	ui_draw_random_overlay(t_random_state *rs, t_camera2d_gol cam)
{
	if (rs->phase == 0)
		rand_phase0(rs, cam);
	else
		rand_phase1(rs, GetScreenWidth(), GetScreenHeight());
}
