/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_menu-2.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:06:08 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 22:44:53 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

bool	ui_draw_credits(void)
{
	t_credit_line	lines[6];
	Rectangle		p;
	int				pw;
	int				ph;

	overlay();
	pw = 420;
	ph = 300;
	p = (Rectangle){(GetScreenWidth() - pw) / 2.0f,
		(GetScreenHeight() - ph) / 2.0f, pw, ph};
	panel_draw(p, ui_c_panel(), ui_c_hi());
	text_c("CREDITS", FXL, (Vector2){p.x + pw / 2, p.y + 34}, ui_c_hi());
	DrawLine((int)p.x + 20, (int)p.y + 58,
		(int)p.x + pw - 20, (int)p.y + 58, ui_c_border());
	credits_init(lines);
	credits_draw_lines(lines, 6, p, pw);
	if (ui_button((Rectangle){p.x + pw / 2 - 65, p.y + ph - 42, 130, 32},
		"Retour", false) == BTN_CLICKED || IsKeyPressed(KEY_ESCAPE))
		return (true);
	return (false);
}
