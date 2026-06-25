/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_browser-2.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:05:17 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/25 08:31:41 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

void	draw_list_scrollbar_thumb(t_list_geom g, t_list_ctx ctx,
			Rectangle thumb)
{
	Vector2	mm;

	mm = GetMousePosition();
	if (ctx.fcount > g.vis && g.vis > 0)
	{
		DrawRectangle(g.sb_x, ctx.list_top, 8, ctx.list_bot - ctx.list_top,
			(Color){30, 30, 48, 200});
		if (g.sb_dragging)
			DrawRectangleRec(thumb, C_HI);
		else if (CheckCollisionPointRec(mm, thumb))
			DrawRectangleRec(thumb, C_BORDER);
		else
			DrawRectangleRec(thumb, (Color){80, 80, 110, 255});
	}
}

Rectangle	handle_scrollbar_drag(t_list_geom *g, t_list_ctx ctx)
{
	Vector2		mm;
	float		sbh;
	float		sby;
	int			ms;
	Rectangle	thumb;

	mm = GetMousePosition();
	ms = ctx.fcount - g->vis;
	if (ms < 0)
		ms = 0;
	thumb = (Rectangle){0, 0, 0, 0};
	if (ctx.fcount > g->vis && g->vis > 0)
	{
		sbh = g->track_h * g->vis / ctx.fcount;
		if (sbh < 20)
			sbh = 20;
		sby = ctx.list_top + (g->track_h - sbh) * (*ctx.scroll) / ms;
		thumb = (Rectangle){(float)g->sb_x, sby, 8, sbh};
		if (IsMouseButtonPressed(0) && CheckCollisionPointRec(mm, thumb))
		{
			g->sb_dragging = true;
			g->sb_drag_y = mm.y;
			g->sb_drag_scroll = *ctx.scroll;
		}
		if (g->sb_dragging)
			*ctx.scroll = g->sb_drag_scroll
				+ (int)((mm.y - g->sb_drag_y) * ms / (g->track_h - sbh));
		if (IsMouseButtonReleased(0))
			g->sb_dragging = false;
	}
	if (*ctx.scroll < 0)
		*ctx.scroll = 0;
	if (*ctx.scroll > ms)
		*ctx.scroll = ms;
	return (thumb);
}

void	draw_list_row_label(t_list_ctx ctx, int ri, Rectangle row, bool hov)
{
	const char	*slash;
	const char	*dname;
	char		folder[32];
	int			fl;
	int			tw;

	slash = strrchr(ctx.names[ri], '/');
	if (slash)
		dname = slash + 1;
	else
		dname = ctx.names[ri];
	if (hov)
		DrawText(dname, (int)row.x + 14, (int)row.y + 7, FS, C_HI);
	else
		DrawText(dname, (int)row.x + 14, (int)row.y + 7, FS, C_TEXT);
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

bool	draw_list_rows(t_list_ctx ctx, t_list_geom g)
{
	Vector2		mm;
	Rectangle	row;
	bool		hov;
	bool		chosen;
	int			i;
	int			ri;
	int			ry;

	mm = GetMousePosition();
	chosen = false;
	*ctx.hovered_idx = -1;
	i = *ctx.scroll;
	while (i < *ctx.scroll + g.vis && i < ctx.fcount)
	{
		ri = ctx.filtered[i];
		ry = ctx.list_top + (i - *ctx.scroll) * g.rh;
		row = (Rectangle){(float)g.lx - 6, (float)ry,
			(float)g.list_w, (float)(g.rh - 2)};
		hov = CheckCollisionPointRec(mm, row);
		if (hov)
			*ctx.hovered_idx = ri;
		if (hov)
			DrawRectangleRec(row, C_HOVER);
		else
			DrawRectangleRec(row, C_PANEL2);
		if (hov)
			DrawRectangleLinesEx(row, 1.0f, C_HI);
		else
			DrawRectangleLinesEx(row, 1.0f, C_BORDER);
		draw_list_row_label(ctx, ri, row, hov);
		if (hov && IsMouseButtonReleased(0))
		{
			snprintf(ctx.out_path, ctx.path_len, "%s", ctx.names[ri]);
			chosen = true;
		}
		i++;
	}
	return (chosen);
}

bool	browser_draw_list(t_list_ctx ctx)
{
	t_list_geom	g;
	Rectangle	thumb;
	Vector2		mm;
	bool		chosen;

	mm = GetMousePosition();
	g.list_w = (int)ctx.p.width - 520 - 8;
	g.rh = 32;
	g.vis = (ctx.list_bot - ctx.list_top) / g.rh;
	g.lx = (int)ctx.p.x + 16;
	g.sb_x = g.lx + g.list_w - 5;
	g.track_h = (float)(ctx.list_bot - ctx.list_top);
	g.sb_dragging = false;
	thumb = handle_scrollbar_drag(&g, ctx);
	if (CheckCollisionPointRec(mm, (Rectangle){ctx.p.x, ctx.p.y + 82,
			(float)(g.list_w + 20), (float)((int)ctx.p.height - 132)}))
		*ctx.scroll -= (int)GetMouseWheelMove();
	chosen = draw_list_rows(ctx, g);
	draw_list_scrollbar_thumb(g, ctx, thumb);
	return (chosen);
}
