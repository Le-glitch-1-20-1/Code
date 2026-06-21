/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_savezone-2.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:14:30 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:20:03 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"
#include "ui_shared.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

void	sz_phase0_input(t_save_zone_state *sz, t_camera2d_gol cam);
void	sz_phase0_draw(t_save_zone_state *sz, t_camera2d_gol cam);

static void	sz_draw_info(t_save_zone_state *sz, Rectangle p, int pw)
{
	char	info[64];
	char	info2[64];

	text_c("SAUVEGARDER LA ZONE", FL, p.x + pw / 2, p.y + 28, C_HI);
	DrawLine((int)p.x + 16, (int)p.y + 50,
		(int)p.x + pw - 16, (int)p.y + 50, C_BORDER);
	snprintf(info, sizeof(info), "Zone : %d x %d  (%d cellules)",
		sz->x1 - sz->x0 + 1, sz->y1 - sz->y0 + 1,
		(sz->x1 - sz->x0 + 1) * (sz->y1 - sz->y0 + 1));
	DrawText(info, (int)p.x + 24, (int)p.y + 60, FS - 1, C_DIM);
	snprintf(info2, sizeof(info2), "Coords : (%d,%d) -> (%d,%d)",
		sz->x0, sz->y0, sz->x1, sz->y1);
	DrawText(info2, (int)p.x + 24, (int)p.y + 78, FS - 2, C_DIM);
	DrawText("Nom du fichier :", (int)p.x + 24, (int)p.y + 98, FS, C_DIM);
	DrawText("(-> assets/patterns/)", (int)p.x + 24, (int)p.y + 116,
		FS - 2, C_DIM);
}

static void	sz_draw_namefield(t_save_zone_state *sz, Rectangle p,
	int pw, bool *editing)
{
	Rectangle	box;
	Vector2		mm;
	char		display[80];

	box = (Rectangle){p.x + 24, p.y + 134, pw - 48, 32};
	DrawRectangleRec(box, C_PANEL2);
	if (*editing)
		DrawRectangleLinesEx(box, 1.0f, C_HI);
	else
		DrawRectangleLinesEx(box, 1.0f, C_BORDER);
	mm = GetMousePosition();
	if (IsMouseButtonReleased(0) && CheckCollisionPointRec(mm, box))
		*editing = true;
	if (IsMouseButtonReleased(0) && !CheckCollisionPointRec(mm, box))
		*editing = false;
	if (*editing)
		sz_name_edit(sz);
	if (sz->name_buf[0])
		snprintf(display, sizeof(display), "%s.rle", sz->name_buf);
	else
		snprintf(display, sizeof(display), "mon_pattern.rle");
	DrawText(display, (int)box.x + 8, (int)box.y + (32 - FS) / 2, FS, C_TEXT);
	if (*editing && (GetTime() * 2 - (int)(GetTime() * 2) < 0.5))
		DrawText("|", (int)box.x + 8 + MeasureText(display, FS),
			(int)box.y + (32 - FS) / 2, FS, C_HI);
}

static bool	sz_phase1(t_save_zone_state *sz, int sw, int sh,
	char *out_path, int path_len)
{
	static bool	editing = false;
	const char	*nm;
	Rectangle	p;
	int			pw;
	int			ph;

	pw = 480;
	ph = 230;
	overlay();
	p = (Rectangle){(sw - pw) / 2.0f, (sh - ph) / 2.0f, pw, ph};
	panel_draw(p, C_PANEL, C_HI);
	sz_draw_info(sz, p, pw);
	sz_draw_namefield(sz, p, pw, &editing);
	if (ui_button((Rectangle){p.x + 24, p.y + ph - 46, 160, 34},
		"Sauvegarder", false) == BTN_CLICKED
		|| (editing && IsKeyPressed(KEY_ENTER)))
	{
		if (sz->name_buf[0])
			nm = sz->name_buf;
		else
			nm = "mon_pattern";
		snprintf(out_path, path_len, "assets/patterns/%s.rle", nm);
		editing = false;
		return (true);
	}
	if (ui_button((Rectangle){p.x + pw - 184, p.y + ph - 46, 160, 34},
		"Annuler", false) == BTN_CLICKED || IsKeyPressed(KEY_ESCAPE))
	{
		editing = false;
		sz->cancelled = true;
	}
	return (false);
}

bool	ui_draw_save_zone(t_save_zone_state *sz, t_camera2d_gol cam,
	char *out_path, int path_len)
{
	int	sw;
	int	sh;

	sw = GetScreenWidth();
	sh = GetScreenHeight();
	if (sz->phase == 0)
	{
		sz_phase0_input(sz, cam);
		sz_phase0_draw(sz, cam);
		if (IsKeyPressed(KEY_ESCAPE))
			sz->cancelled = true;
		return (false);
	}
	return (sz_phase1(sz, sw, sh, out_path, path_len));
}
