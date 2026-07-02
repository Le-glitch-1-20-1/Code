/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_savezone-2.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:14:30 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 22:49:56 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

void	sz_draw_info(t_save_zone_state *sz, Rectangle p, int pw)
{
	char	info[64];
	char	info2[64];

	text_c("SAUVEGARDER LA ZONE", FL, (Vector2){p.x + pw / 2, p.y + 28},
		ui_c_hi());
	DrawLine((int)p.x + 16, (int)p.y + 50,
		(int)p.x + pw - 16, (int)p.y + 50, ui_c_border());
	snprintf(info, sizeof(info), "Zone : %d x %d  (%d cellules)",
		sz->x1 - sz->x0 + 1, sz->y1 - sz->y0 + 1,
		(sz->x1 - sz->x0 + 1) * (sz->y1 - sz->y0 + 1));
	DrawText(info, (int)p.x + 24, (int)p.y + 60, FS - 1, ui_c_dim());
	snprintf(info2, sizeof(info2), "Coords : (%d,%d) -> (%d,%d)",
		sz->x0, sz->y0, sz->x1, sz->y1);
	DrawText(info2, (int)p.x + 24, (int)p.y + 78, FS - 2, ui_c_dim());
	DrawText("Nom du fichier :", (int)p.x + 24, (int)p.y + 98, FS, ui_c_dim());
	DrawText("(-> assets/patterns/)", (int)p.x + 24, (int)p.y + 116,
		FS - 2, ui_c_dim());
}

static void	sz_draw_name_text(Rectangle box, t_save_zone_state *sz,
				bool editing)
{
	char	display[80];

	if (sz->name_buf[0])
		snprintf(display, sizeof(display), "%s.rle", sz->name_buf);
	else
		snprintf(display, sizeof(display), "mon_pattern.rle");
	DrawText(display, (int)box.x + 8, (int)box.y + (32 - FS) / 2, FS,
		ui_c_text());
	if (editing && (GetTime() * 2 - (int)(GetTime() * 2) < 0.5))
		DrawText("|", (int)box.x + 8 + MeasureText(display, FS),
			(int)box.y + (32 - FS) / 2, FS, ui_c_hi());
}

void	sz_draw_namefield(t_save_zone_state *sz, Rectangle p, int pw,
			bool *editing)
{
	Rectangle	box;

	box = (Rectangle){p.x + 24, p.y + 134, pw - 48, 32};
	DrawRectangleRec(box, ui_c_panel2());
	if (*editing)
		DrawRectangleLinesEx(box, 1.0f, ui_c_hi());
	else
		DrawRectangleLinesEx(box, 1.0f, ui_c_border());
	if (IsMouseButtonReleased(0) && CheckCollisionPointRec(GetMousePosition(),
			box))
		*editing = true;
	if (IsMouseButtonReleased(0) && !CheckCollisionPointRec(GetMousePosition(),
			box))
		*editing = false;
	if (*editing)
		sz_name_edit(sz);
	sz_draw_name_text(box, sz, *editing);
}
