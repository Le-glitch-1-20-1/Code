/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_menu-1.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:17:24 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 09:18:42 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

static void	menu_init_items(t_menu_item *items)
{
	items[0].l = "Reprendre";
	items[0].a = MENU_RESUME;
	items[1].l = "Touches";
	items[1].a = MENU_KEYBINDS;
	items[2].l = "Credits";
	items[2].a = MENU_CREDITS;
	items[3].l = "Quitter";
	items[3].a = MENU_QUIT;
}

static t_menu_action	menu_draw_panel(t_menu_item *items, Rectangle p,
	int pw, int ph)
{
	t_menu_action	act;
	float			bw;
	float			bh2;
	float			gap;
	int				i;

	text_c("MENU", FXL, p.x + pw / 2, p.y + 36, C_HI);
	DrawLine((int)p.x + 10, (int)p.y + 62,
		(int)p.x + pw - 10, (int)p.y + 62, C_BORDER);
	act = MENU_NONE;
	bw = pw - 50;
	bh2 = 42;
	gap = 10;
	i = 0;
	while (i < 4)
	{
		if (ui_button((Rectangle){p.x + 25, p.y + 78 + i * (bh2 + gap),
				bw, bh2}, items[i].l, false) == BTN_CLICKED)
			act = items[i].a;
		i++;
	}
	(void)ph;
	return (act);
}

t_menu_action	ui_draw_menu(void)
{
	t_menu_item		items[4];
	t_menu_action	act;
	Rectangle		p;
	int				pw;
	int				ph;

	overlay();
	pw = 340;
	ph = 290;
	p = (Rectangle){(GetScreenWidth() - pw) / 2.0f,
		(GetScreenHeight() - ph) / 2.0f, pw, ph};
	panel_draw(p, C_PANEL, C_HI);
	menu_init_items(items);
	act = menu_draw_panel(items, p, pw, ph);
	if (IsKeyPressed(KEY_ESCAPE))
		act = MENU_RESUME;
	return (act);
}

void	credits_init(t_credit_line *lines)
{
	lines[0].l = "Jeu";
	lines[0].v = "Jeu de la Vie - Conway";
	lines[0].c = C_TEXT;
	lines[1].l = "Auteur";
	lines[1].v = "Toi !";
	lines[1].c = C_ACCENT2;
	lines[2].l = "Moteur";
	lines[2].v = "raylib 5.0";
	lines[2].c = C_HI;
	lines[3].l = "Langue";
	lines[3].v = "C11";
	lines[3].c = C_TEXT;
	lines[4].l = "Grille";
	lines[4].v = "Infinie (chunks 16x16)";
	lines[4].c = C_TEXT;
	lines[5].l = "Saves";
	lines[5].v = "Format RLE compatible Golly";
	lines[5].c = C_TEXT;
}

void	credits_draw_lines(t_credit_line *lines, int n, Rectangle p,
	int pw)
{
	int	i;
	int	y;
	int	vw;

	i = 0;
	while (i < n)
	{
		y = (int)p.y + 70 + i * 26;
		DrawText(lines[i].l, (int)p.x + 26, y, FS, C_DIM);
		vw = MeasureText(lines[i].v, FS);
		DrawText(lines[i].v, (int)p.x + pw - 26 - vw, y, FS, lines[i].c);
		i++;
	}
}
