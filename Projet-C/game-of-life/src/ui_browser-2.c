/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_browser-2.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:05:17 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 12:00:00 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

Rectangle	scrollbar_thumb_rect(t_list_geom *g, t_list_ctx ctx)
{
	float	sbh;
	float	sby;
	int		ms;

	ms = ctx.fcount - g->vis;
	if (ms < 0)
		ms = 0;
	sbh = g->track_h * g->vis / ctx.fcount;
	if (sbh < 20)
		sbh = 20;
	sby = ctx.list_top + (g->track_h - sbh) * (*ctx.scroll) / ms;
	return ((Rectangle){(float)g->sb_x, sby, 8, sbh});
}

void	scrollbar_clamp(t_list_geom *g, t_list_ctx ctx)
{
	int	ms;

	ms = ctx.fcount - g->vis;
	if (ms < 0)
		ms = 0;
	if (*ctx.scroll < 0)
		*ctx.scroll = 0;
	if (*ctx.scroll > ms)
		*ctx.scroll = ms;
}

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
			DrawRectangleRec(thumb, ui_c_hi());
		else if (CheckCollisionPointRec(mm, thumb))
			DrawRectangleRec(thumb, ui_c_border());
		else
			DrawRectangleRec(thumb, (Color){80, 80, 110, 255});
	}
}

static float	sb_denominator(t_list_geom *g, Rectangle thumb)
{
	if (thumb.height > 0)
		return (g->track_h - thumb.height);
	return (1);
}

Rectangle	handle_scrollbar_drag(t_list_geom *g, t_list_ctx ctx)
{
	Vector2		mm;
	int			ms;
	Rectangle	thumb;

	mm = GetMousePosition();
	thumb = (Rectangle){0, 0, 0, 0};
	if (ctx.fcount > g->vis && g->vis > 0)
	{
		thumb = scrollbar_thumb_rect(g, ctx);
		ms = ctx.fcount - g->vis;
		if (IsMouseButtonPressed(0) && CheckCollisionPointRec(mm, thumb))
		{
			g->sb_dragging = true;
			g->sb_drag_y = mm.y;
			g->sb_drag_scroll = *ctx.scroll;
		}
		if (g->sb_dragging)
			*ctx.scroll = g->sb_drag_scroll
				+ (int)((mm.y - g->sb_drag_y) * ms
					/ sb_denominator(g, thumb));
		if (IsMouseButtonReleased(0))
			g->sb_dragging = false;
	}
	scrollbar_clamp(g, ctx);
	return (thumb);
}
