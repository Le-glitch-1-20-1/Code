/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_browser-6.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:05:17 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 08:36:40 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

void	draw_list_row_folder(t_list_ctx ctx, int ri, Rectangle row,
			const char *slash)
{
	char	folder[32];
	int		fl;
	int		tw;

	folder[0] = 0;
	if (slash)
	{
		fl = (int)(slash - ctx.names[ri]);
		if (fl < 31)
		{
			memcpy(folder, ctx.names[ri], fl);
			folder[fl] = 0;
		}
	}
	if (folder[0])
	{
		tw = MeasureText(folder, FS - 3);
		DrawText(folder, (int)row.x + row.width - tw - 8,
			(int)row.y + 9, FS - 3, C_DIM);
	}
}

void	draw_list_row_label(t_list_ctx ctx, int ri, Rectangle row, bool hov)
{
	const char	*slash;
	const char	*dname;

	slash = strrchr(ctx.names[ri], '/');
	if (slash)
		dname = slash + 1;
	else
		dname = ctx.names[ri];
	if (hov)
		DrawText(dname, (int)row.x + 14, (int)row.y + 7, FS, C_HI);
	else
		DrawText(dname, (int)row.x + 14, (int)row.y + 7, FS, C_TEXT);
	draw_list_row_folder(ctx, ri, row, slash);
}

static void	draw_list_row_bg(Rectangle row, bool hov)
{
	if (hov)
		DrawRectangleRec(row, C_HOVER);
	else
		DrawRectangleRec(row, C_PANEL2);
	if (hov)
		DrawRectangleLinesEx(row, 1.0f, C_HI);
	else
		DrawRectangleLinesEx(row, 1.0f, C_BORDER);
}

bool	draw_list_row(t_list_ctx ctx, t_list_geom g, int i)
{
	Rectangle	row;
	bool		hov;
	int			ri;

	ri = ctx.filtered[i];
	row = (Rectangle){(float)g.lx - 6,
		(float)(ctx.list_top + (i - *ctx.scroll) * g.rh),
		(float)g.list_w, (float)(g.rh - 2)};
	hov = CheckCollisionPointRec(GetMousePosition(), row);
	if (hov)
		*ctx.hovered_idx = ri;
	draw_list_row_bg(row, hov);
	draw_list_row_label(ctx, ri, row, hov);
	if (hov && IsMouseButtonReleased(0))
	{
		snprintf(ctx.out_path, ctx.path_len, "%s", ctx.names[ri]);
		return (true);
	}
	return (false);
}

bool	draw_list_rows(t_list_ctx ctx, t_list_geom g)
{
	bool	chosen;
	int		i;

	chosen = false;
	*ctx.hovered_idx = -1;
	i = *ctx.scroll;
	while (i < *ctx.scroll + g.vis && i < ctx.fcount)
	{
		if (draw_list_row(ctx, g, i))
			chosen = true;
		i++;
	}
	return (chosen);
}

bool	browser_draw_list(t_list_ctx ctx)
{
	t_list_geom	g;
	Rectangle	thumb;
	bool		chosen;

	g.list_w = (int)ctx.p.width - 520 - 8;
	g.rh = 32;
	g.vis = (ctx.list_bot - ctx.list_top) / g.rh;
	g.lx = (int)ctx.p.x + 16;
	g.sb_x = g.lx + g.list_w - 5;
	g.track_h = (float)(ctx.list_bot - ctx.list_top);
	g.sb_dragging = false;
	thumb = handle_scrollbar_drag(&g, ctx);
	if (CheckCollisionPointRec(GetMousePosition(), (Rectangle){ctx.p.x,
		ctx.p.y + 82, (float)(g.list_w + 20),
		(float)((int)ctx.p.height - 132)}))
		*ctx.scroll -= (int)GetMouseWheelMove();
	chosen = draw_list_rows(ctx, g);
	draw_list_scrollbar_thumb(g, ctx, thumb);
	return (chosen);
}
