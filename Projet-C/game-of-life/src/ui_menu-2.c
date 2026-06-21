/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_menu-2.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:06:08 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:06:09 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"
#include "ui_shared.h"
#include <string.h>

void	credits_init(t_credit_line *lines);
void	credits_draw_lines(t_credit_line *lines, int n, Rectangle p, int pw);

bool	ui_draw_credits(void)
{
	t_credit_line	lines[6];
	Rectangle		p;
	int				sw;
	int				sh;
	int				pw;
	int				ph;

	overlay();
	sw = GetScreenWidth();
	sh = GetScreenHeight();
	pw = 420;
	ph = 300;
	p = (Rectangle){(sw - pw) / 2.0f, (sh - ph) / 2.0f, pw, ph};
	panel_draw(p, C_PANEL, C_HI);
	text_c("CREDITS", FXL, p.x + pw / 2, p.y + 34, C_HI);
	DrawLine((int)p.x + 20, (int)p.y + 58,
		(int)p.x + pw - 20, (int)p.y + 58, C_BORDER);
	credits_init(lines);
	credits_draw_lines(lines, 6, p, pw);
	if (ui_button((Rectangle){p.x + pw / 2 - 65, p.y + ph - 42, 130, 32},
		"Retour", false) == BTN_CLICKED || IsKeyPressed(KEY_ESCAPE))
		return (true);
	return (false);
}
