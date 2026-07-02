/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_browser-8.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/27 21:05:20 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 21:05:20 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

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
	Rectangle	wheel_zone;

	g.list_w = (int)ctx.p.width - 520 - 8;
	g.rh = 32;
	g.vis = (ctx.list_bot - ctx.list_top) / g.rh;
	g.lx = (int)ctx.p.x + 16;
	g.sb_x = g.lx + g.list_w - 5;
	g.track_h = (float)(ctx.list_bot - ctx.list_top);
	g.sb_dragging = false;
	thumb = handle_scrollbar_drag(&g, ctx);
	wheel_zone = (Rectangle){ctx.p.x, ctx.p.y + 82,
		(float)(g.list_w + 20), (float)((int)ctx.p.height - 132)};
	if (CheckCollisionPointRec(GetMousePosition(), wheel_zone))
		*ctx.scroll -= (int)GetMouseWheelMove();
	chosen = draw_list_rows(ctx, g);
	draw_list_scrollbar_thumb(g, ctx, thumb);
	return (chosen);
}
