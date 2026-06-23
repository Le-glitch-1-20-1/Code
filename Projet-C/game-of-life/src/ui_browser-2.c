/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_browser-2.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:05:17 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 23:05:10 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

bool	browser_draw_list(char names[MAX_RLE][128], int *filtered,
	int fcount, Rectangle p, int list_top, int list_bot, int *scroll,
	int *hovered_idx, char *out_path, int path_len)
{
	int				rh;
	int				vis;
	int				lx;
	int				ms;
	bool			chosen;
	int				i;
	int				ri;
	int				ry;
	int				tw;
	int				fl;
	float			sbh;
	float			sby;
	bool			hov;
	Vector2			mm;
	Rectangle		row;
	const char		*slash;
	const char		*dname;
	char			folder[32];
	int				list_w;
	static bool		sb_dragging = false;
	static float	sb_drag_y = 0;
	static int		sb_drag_scroll = 0;
	int				sb_x;
	float			track_h;
	Rectangle		sb_thumb_r;

	list_w = (int)p.width - 520 - 8;
	rh = 32;
	vis = (list_bot - list_top) / rh;
	lx = (int)p.x + 16;
	mm = GetMousePosition();
	sb_x = lx + list_w - 5;
	track_h = (float)(list_bot - list_top);
	ms = fcount - vis;
	if (ms < 0)
		ms = 0;
	sb_thumb_r = (Rectangle){0, 0, 0, 0};
	if (fcount > vis && vis > 0)
	{
		sbh = track_h * vis / fcount;
		if (sbh < 20)
			sbh = 20;
		sby = list_top + (track_h - sbh) * (*scroll) / ms;
		sb_thumb_r = (Rectangle){(float)sb_x, sby, 8, sbh};
		if (IsMouseButtonPressed(0)
			&& CheckCollisionPointRec(mm, sb_thumb_r))
		{
			sb_dragging = true;
			sb_drag_y = mm.y;
			sb_drag_scroll = *scroll;
		}
		if (sb_dragging)
			*scroll = sb_drag_scroll
				+ (int)((mm.y - sb_drag_y) * ms / (track_h - sbh));
		if (IsMouseButtonReleased(0))
			sb_dragging = false;
	}
	if (CheckCollisionPointRec(mm, (Rectangle){p.x, p.y + 82,
			(float)(list_w + 20), (float)((int)p.height - 132)}))
		*scroll -= (int)GetMouseWheelMove();
	if (*scroll < 0)
		*scroll = 0;
	if (*scroll > ms)
		*scroll = ms;
	*hovered_idx = -1;
	chosen = false;
	i = *scroll;
	while (i < *scroll + vis && i < fcount)
	{
		ri = filtered[i];
		ry = list_top + (i - *scroll) * rh;
		row = (Rectangle){(float)lx - 6, (float)ry,
			(float)list_w, (float)(rh - 2)};
		hov = CheckCollisionPointRec(mm, row);
		if (hov)
			*hovered_idx = ri;
		if (hov)
			DrawRectangleRec(row, C_HOVER);
		else
			DrawRectangleRec(row, C_PANEL2);
		if (hov)
			DrawRectangleLinesEx(row, 1.0f, C_HI);
		else
			DrawRectangleLinesEx(row, 1.0f, C_BORDER);
		slash = strrchr(names[ri], '/');
		if (slash)
			dname = slash + 1;
		else
			dname = names[ri];
		if (hov)
			DrawText(dname, lx + 8, ry + (rh - 2 - FS) / 2, FS, C_HI);
		else
			DrawText(dname, lx + 8, ry + (rh - 2 - FS) / 2, FS, C_TEXT);
		folder[0] = 0;
		if (slash)
		{
			fl = (int)(slash - names[ri]);
			if (fl < 31)
			{
				memcpy(folder, names[ri], fl);
				folder[fl] = 0;
			}
		}
		if (folder[0])
		{
			tw = MeasureText(folder, FS - 3);
			DrawText(folder, lx + list_w - tw - 14,
				ry + (rh - 2 - FS) / 2 + 2, FS - 3, C_DIM);
		}
		if (hov && IsMouseButtonReleased(0))
		{
			snprintf(out_path, path_len, "%s", names[ri]);
			chosen = true;
		}
		i++;
	}
	if (fcount > vis && vis > 0)
	{
		DrawRectangle(sb_x, list_top, 8, list_bot - list_top,
			(Color){30, 30, 48, 200});
		if (sb_dragging)
			DrawRectangleRec(sb_thumb_r, C_HI);
		else if (CheckCollisionPointRec(mm, sb_thumb_r))
			DrawRectangleRec(sb_thumb_r, C_BORDER);
		else
			DrawRectangleRec(sb_thumb_r, (Color){80, 80, 110, 255});
	}
	return (chosen);
}

bool	ui_draw_load_browser(char *out_path, int path_len)
{
	static char	names[MAX_RLE][128];
	static int	count = -1;
	static int	scroll = 0;
	static char	search[64] = "";
	static bool	search_edit = false;
	static int	hovered_idx = -1;
	int			sw;
	int			sh;
	int			pw;
	int			ph;
	int			list_top;
	int			list_bot;
	int			filtered[MAX_RLE];
	int			fcount;
	bool		chosen;
	int			prx;
	Rectangle	p;
	Rectangle	pr;
	Rectangle	pdest;

	overlay();
	sw = GetScreenWidth();
	sh = GetScreenHeight();
	pw = 970;
	if (sh - 80 < 580)
		ph = sh - 80;
	else
		ph = 580;
	p = (Rectangle){(sw - pw) / 2.0f, (sh - ph) / 2.0f, pw, ph};
	panel_draw(p, C_PANEL, C_HI);
	text_c("CHARGER UN PATTERN", FL, p.x + pw / 2, p.y + 26, C_HI);
	DrawLine((int)p.x + 10, (int)p.y + 48,
		(int)p.x + pw - 10, (int)p.y + 48, C_BORDER);
	if (count < 0)
	{
		browser_load_files(names, &count);
		scroll = 0;
	}
	list_top = (int)p.y + 82;
	list_bot = (int)p.y + ph - 50;
	browser_draw_search(p, pw, search, &search_edit, &scroll);
	fcount = browser_filter(names, count, filtered, search);
	chosen = browser_draw_list(names, filtered, fcount, p,
			list_top, list_bot, &scroll, &hovered_idx, out_path, path_len);
	if (fcount == 0 && count == 0)
	{
		text_c("Aucun fichier .rle trouve.", FS,
			p.x + (pw - 530) / 2 + 16, p.y + ph / 2, C_DIM);
		text_c("Placez vos .rle dans assets/patterns/", FS - 2,
			p.x + (pw - 530) / 2 + 16, p.y + ph / 2 + 22, C_DIM);
	}
	else if (fcount == 0)
		text_c("Aucun resultat.", FS,
			p.x + (pw - 530) / 2 + 16, p.y + ph / 2, C_DIM);
	if (chosen)
	{
		count = -1;
		scroll = 0;
		search[0] = 0;
		search_edit = false;
		return (true);
	}
	prx = (int)p.x + 16 + (pw - 530) + 8;
	pr = (Rectangle){(float)prx, (float)list_top,
		(float)(500 - 8), (float)(list_bot - list_top)};
	panel_draw(pr, (Color){10, 10, 15, 255}, C_BORDER);
	text_c("Apercu", FS - 1, pr.x + pr.width / 2, pr.y + 12, C_DIM);
	if (hovered_idx >= 0)
	{
		pdest = (Rectangle){pr.x + 6, pr.y + 24,
			pr.width - 12, (float)(list_bot - list_top) - 36};
		draw_rle_preview(names[hovered_idx], pdest);
	}
	else
	{
		text_c("Survolez un", FS - 2, pr.x + pr.width / 2,
			pr.y + (list_bot - list_top) / 2 - 10, C_DIM);
		text_c("fichier pour", FS - 2, pr.x + pr.width / 2,
			pr.y + (list_bot - list_top) / 2 + 8, C_DIM);
		text_c("l'apercu", FS - 2, pr.x + pr.width / 2,
			pr.y + (list_bot - list_top) / 2 + 26, C_DIM);
	}
	if (ui_button((Rectangle){p.x + pw / 2 - 65, p.y + ph - 42, 130, 32},
		"Annuler", false) == BTN_CLICKED || IsKeyPressed(KEY_ESCAPE))
	{
		count = -1;
		scroll = 0;
		search[0] = 0;
		search_edit = false;
		return (false);
	}
	return (false);
}
