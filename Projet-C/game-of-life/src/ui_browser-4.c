/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_browser-4.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:05:17 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/25 08:33:22 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

t_browser_view	browser_layout(void)
{
	t_browser_view	v;
	int				sw;
	int				sh;

	sw = GetScreenWidth();
	sh = GetScreenHeight();
	v.pw = 970;
	if (sh - 80 < 580)
		v.ph = sh - 80;
	else
		v.ph = 580;
	v.p = (Rectangle){(sw - v.pw) / 2.0f, (sh - v.ph) / 2.0f,
		(float)v.pw, (float)v.ph};
	v.list_top = (int)v.p.y + 82;
	v.list_bot = (int)v.p.y + v.ph - 50;
	return (v);
}

void	draw_no_results(t_browser_view v, int fcount, int count)
{
	if (fcount == 0 && count == 0)
	{
		text_c("Aucun fichier .rle trouve.", FS,
			v.p.x + (v.pw - 530) / 2 + 16, v.p.y + v.ph / 2, C_DIM);
		text_c("Placez vos .rle dans assets/patterns/", FS - 2,
			v.p.x + (v.pw - 530) / 2 + 16, v.p.y + v.ph / 2 + 22, C_DIM);
	}
	else if (fcount == 0)
		text_c("Aucun resultat.", FS,
			v.p.x + (v.pw - 530) / 2 + 16, v.p.y + v.ph / 2, C_DIM);
}

void	browser_draw_preview(t_browser_view v, char names[MAX_RLE][128],
			int hovered_idx)
{
	Rectangle	pr;
	Rectangle	pdest;
	int			prx;
	int			lh;

	prx = (int)v.p.x + 16 + (v.pw - 530) + 8;
	lh = v.list_bot - v.list_top;
	pr = (Rectangle){(float)prx, (float)v.list_top, (float)(500 - 8),
		(float)lh};
	panel_draw(pr, (Color){10, 10, 15, 255}, C_BORDER);
	text_c("Apercu", FS - 1, pr.x + pr.width / 2, pr.y + 12, C_DIM);
	if (hovered_idx >= 0)
	{
		pdest = (Rectangle){pr.x + 6, pr.y + 24, pr.width - 12,
			(float)lh - 36};
		draw_rle_preview(names[hovered_idx], pdest);
	}
	else
	{
		text_c("Survolez un", FS - 2, pr.x + pr.width / 2,
			pr.y + lh / 2 - 10, C_DIM);
		text_c("fichier pour", FS - 2, pr.x + pr.width / 2,
			pr.y + lh / 2 + 8, C_DIM);
		text_c("l'apercu", FS - 2, pr.x + pr.width / 2,
			pr.y + lh / 2 + 26, C_DIM);
	}
}

void	reset_browser_state(int *count, int *scroll, char *search,
			bool *search_edit)
{
	*count = -1;
	*scroll = 0;
	search[0] = 0;
	*search_edit = false;
}

bool	ui_draw_load_browser(char *out_path, int path_len)
{
	static char	names[MAX_RLE][128];
	static int	count = -1;
	static int	scroll = 0;
	static char	search[64] = "";
	static bool	search_edit = false;
	static int	hovered_idx = -1;
	t_browser_view	v;
	int				filtered[MAX_RLE];
	int				fcount;
	bool			chosen;

	overlay();
	v = browser_layout();
	panel_draw(v.p, C_PANEL, C_HI);
	text_c("CHARGER UN PATTERN", FL, v.p.x + v.pw / 2, v.p.y + 26, C_HI);
	DrawLine((int)v.p.x + 10, (int)v.p.y + 48,
		(int)v.p.x + v.pw - 10, (int)v.p.y + 48, C_BORDER);
	if (count < 0)
	{
		browser_load_files(names, &count);
		scroll = 0;
	}
	browser_draw_search(v.p, v.pw, (t_search_state){search,
		&search_edit, &scroll});
	fcount = browser_filter(names, count, filtered, search);
	chosen = browser_draw_list((t_list_ctx){names, filtered, fcount, v.p,
		v.list_top, v.list_bot, &scroll, &hovered_idx, out_path, path_len});
	draw_no_results(v, fcount, count);
	if (chosen)
	{
		reset_browser_state(&count, &scroll, search, &search_edit);
		return (true);
	}
	browser_draw_preview(v, names, hovered_idx);
	if (ui_button((Rectangle){v.p.x + v.pw / 2 - 65, v.p.y + v.ph - 42,
			130, 32}, "Annuler", false) == BTN_CLICKED
		|| IsKeyPressed(KEY_ESCAPE))
	{
		reset_browser_state(&count, &scroll, search, &search_edit);
		return (false);
	}
	return (false);
}
