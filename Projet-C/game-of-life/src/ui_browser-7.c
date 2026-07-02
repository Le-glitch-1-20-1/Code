/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_browser-7.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:05:17 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 08:37:52 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

void	preview_no_hover_msg(Rectangle pr, int lh)
{
	text_c("Survolez un", FS - 2, (Vector2){pr.x + pr.width / 2,
		pr.y + lh / 2 - 10}, ui_c_dim());
	text_c("fichier pour", FS - 2, (Vector2){pr.x + pr.width / 2,
		pr.y + lh / 2 + 8}, ui_c_dim());
	text_c("l'apercu", FS - 2, (Vector2){pr.x + pr.width / 2,
		pr.y + lh / 2 + 26}, ui_c_dim());
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
	panel_draw(pr, (Color){10, 10, 15, 255}, ui_c_border());
	text_c("Apercu", FS - 1, (Vector2){pr.x + pr.width / 2, pr.y + 12},
		ui_c_dim());
	if (hovered_idx >= 0)
	{
		pdest = (Rectangle){pr.x + 6, pr.y + 24, pr.width - 12,
			(float)lh - 36};
		draw_rle_preview(names[hovered_idx], pdest);
	}
	else
		preview_no_hover_msg(pr, lh);
}

static bool	browser_finish(t_browser_view v, int *count,
				t_search_state st)
{
	if (ui_button((Rectangle){v.p.x + v.pw / 2 - 65, v.p.y + v.ph - 42,
			130, 32}, "Annuler", false) == BTN_CLICKED
		|| IsKeyPressed(KEY_ESCAPE))
	{
		reset_browser_state(count, st.scroll, st.search, st.search_edit);
		return (true);
	}
	return (false);
}

static bool	browser_draw_content(t_browser_view v, char names[MAX_RLE][128],
				t_search_state st, t_browser_ctx bc)
{
	int		filtered[MAX_RLE];
	int		fcount;
	int		hovered_idx;
	bool	chosen;

	hovered_idx = -1;
	browser_draw_search(v.p, v.pw, st);
	fcount = browser_filter(names, *bc.count, filtered, st.search);
	chosen = browser_draw_list((t_list_ctx){names, filtered, fcount, v.p,
			v.list_top, v.list_bot, st.scroll, &hovered_idx, bc.out_path,
			bc.path_len});
	draw_no_results(v, fcount, *bc.count);
	browser_draw_preview(v, names, hovered_idx);
	if (chosen)
	{
		reset_browser_state(bc.count, st.scroll, st.search, st.search_edit);
		return (true);
	}
	return (false);
}

bool	ui_draw_load_browser(char *out_path, int path_len)
{
	static char				names[MAX_RLE][128];
	static int				count = -1;
	static t_browser_state	bs;
	t_browser_view			v;

	overlay();
	v = browser_layout();
	draw_browser_header(v);
	if (count < 0)
	{
		browser_load_files(names, &count);
		bs.scroll = 0;
	}
	if (browser_draw_content(v, names,
			(t_search_state){bs.search, &bs.search_edit, &bs.scroll},
		(t_browser_ctx){&count, out_path, path_len}))
		return (true);
	if (browser_finish(v, &count,
			(t_search_state){bs.search, &bs.search_edit, &bs.scroll}))
		return (false);
	return (false);
}
