/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_browser-3.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:04:57 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 08:34:05 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

static void	search_box_append_chars(t_search_state st)
{
	int	k;
	int	l;

	k = GetCharPressed();
	while (k > 0)
	{
		l = (int)strlen(st.search);
		if (l < 60)
		{
			st.search[l] = (char)k;
			st.search[l + 1] = 0;
		}
		k = GetCharPressed();
	}
}

void	search_box_input(t_search_state st, Rectangle sbox)
{
	Vector2	mm;
	int		l;

	mm = GetMousePosition();
	if (IsMouseButtonReleased(0) && CheckCollisionPointRec(mm, sbox))
		*st.search_edit = true;
	if (IsMouseButtonReleased(0) && !CheckCollisionPointRec(mm, sbox))
		*st.search_edit = false;
	if (!*st.search_edit)
		return ;
	search_box_append_chars(st);
	if (IsKeyPressed(KEY_BACKSPACE))
	{
		l = (int)strlen(st.search);
		if (l > 0)
		{
			st.search[l - 1] = 0;
			*st.scroll = 0;
		}
	}
}

void	search_box_text(t_search_state st, int lx3, int py)
{
	int	tw;

	if (st.search[0])
		DrawText(st.search, lx3 + 4, py, FS, ui_c_text());
	else
		DrawText("...", lx3 + 4, py, FS, ui_c_dim());
	if (*st.search_edit && (GetTime() * 2 - (int)(GetTime() * 2) < 0.5))
	{
		tw = MeasureText(st.search, FS);
		DrawText("|", lx3 + 4 + tw, py, FS, ui_c_hi());
	}
}

void	browser_draw_search(Rectangle p, int pw, t_search_state st)
{
	Rectangle	sbox;
	int			lx3;
	int			sw4;

	DrawText("Recherche:", (int)p.x + 16, (int)p.y + 56, FS, ui_c_dim());
	lx3 = (int)p.x + 16 + MeasureText("Recherche:", FS) + 8;
	sw4 = (int)p.x + 16 + (pw - 30) - lx3;
	sbox = (Rectangle){(float)lx3, (float)((int)p.y + 54),
		(float)sw4, (float)(FS + 8)};
	DrawRectangleRec(sbox, ui_c_panel2());
	if (*st.search_edit)
		DrawRectangleLinesEx(sbox, 1.0f, ui_c_hi());
	else
		DrawRectangleLinesEx(sbox, 1.0f, ui_c_border());
	search_box_input(st, sbox);
	search_box_text(st, lx3, (int)p.y + 56);
}
