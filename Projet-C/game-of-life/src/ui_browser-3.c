/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_browser-1b.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:04:57 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 11:21:56 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

void	browser_draw_search(Rectangle p, int pw, t_search_state st)
{
	Rectangle	sbox;
	Vector2		mm;
	int			lx3;
	int			sw3;
	int			sw4;
	int			tw;
	int			k;
	int			l;

	DrawText("Recherche:", (int)p.x + 16, (int)p.y + 56, FS, C_DIM);
	lx3 = (int)p.x + 16 + MeasureText("Recherche:", FS) + 8;
	sw3 = pw - 30;
	sw4 = (int)p.x + 16 + sw3 - lx3;
	sbox = (Rectangle){(float)lx3, (float)((int)p.y + 54),
		(float)sw4, (float)(FS + 8)};
	DrawRectangleRec(sbox, C_PANEL2);
	if (*st.search_edit)
		DrawRectangleLinesEx(sbox, 1.0f, C_HI);
	else
		DrawRectangleLinesEx(sbox, 1.0f, C_BORDER);
	mm = GetMousePosition();
	if (IsMouseButtonReleased(0) && CheckCollisionPointRec(mm, sbox))
		*st.search_edit = true;
	if (IsMouseButtonReleased(0) && !CheckCollisionPointRec(mm, sbox))
		*st.search_edit = false;
	if (*st.search_edit)
	{
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
	if (st.search[0])
		DrawText(st.search, lx3 + 4, (int)p.y + 56, FS, C_TEXT);
	else
		DrawText("...", lx3 + 4, (int)p.y + 56, FS, C_DIM);
	if (*st.search_edit && (GetTime() * 2 - (int)(GetTime() * 2) < 0.5))
	{
		tw = MeasureText(st.search, FS);
		DrawText("|", lx3 + 4 + tw, (int)p.y + 56, FS, C_HI);
	}
}
