/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_savezone-5.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/27 21:05:20 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 21:05:20 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

static t_bbox	sz_normalize_box(t_save_zone_state *sz)
{
	t_bbox	box;

	box = (t_bbox){sz->x0, sz->y0, sz->x1, sz->y1};
	if (box.x0 > box.x1)
	{
		box.x0 = sz->x1;
		box.x1 = sz->x0;
	}
	if (box.y0 > box.y1)
	{
		box.y0 = sz->y1;
		box.y1 = sz->y0;
	}
	return (box);
}

static void	sz_draw_info_box(t_bbox box)
{
	char	info1[80];
	char	info2[80];

	snprintf(info1, sizeof(info1), "Export RLE : %d x %d",
		box.x1 - box.x0 + 1, box.y1 - box.y0 + 1);
	snprintf(info2, sizeof(info2), "Cellules : %d",
		(box.x1 - box.x0 + 1) * (box.y1 - box.y0 + 1));
	DrawRectangle(10, 50, 240, 50, (Color){14, 14, 22, 210});
	DrawRectangleLinesEx((Rectangle){10, 50, 240, 50}, 1.5f,
		(Color){127, 119, 221, 180});
	DrawText(info1, 18, 58, 15, (Color){200, 200, 255, 240});
	DrawText(info2, 18, 78, 15, (Color){200, 200, 255, 240});
}

void	sz_draw_dragging(t_save_zone_state *sz, t_camera2d_gol cam)
{
	t_bbox		box;
	Rectangle	r;

	box = sz_normalize_box(sz);
	r.x = box.x0 * cam.zoom + cam.offset.x;
	r.y = box.y0 * cam.zoom + cam.offset.y;
	r.width = (box.x1 - box.x0 + 1) * cam.zoom;
	r.height = (box.y1 - box.y0 + 1) * cam.zoom;
	DrawRectangle((int)r.x, (int)r.y, (int)r.width, (int)r.height,
		(Color){221, 185, 60, 30});
	DrawRectangleLinesEx(r, 2.0f, (Color){221, 185, 60, 220});
	sz_draw_info_box(box);
}

void	sz_phase0_draw(t_save_zone_state *sz, t_camera2d_gol cam)
{
	if (!sz->dragging)
	{
		sz_draw_empty();
		return ;
	}
	sz_draw_dragging(sz, cam);
}
