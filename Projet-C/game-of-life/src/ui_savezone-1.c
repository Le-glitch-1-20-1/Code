/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_savezone-1.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:06:43 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 22:48:16 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

void	sz_phase0_input(t_save_zone_state *sz, t_camera2d_gol cam)
{
	Vector2	m;
	bool	on_ui;
	int		t;

	m = GetMousePosition();
	on_ui = (m.y < 42);
	if (!on_ui && IsMouseButtonPressed(MOUSE_BUTTON_LEFT))
	{
		sz->dragging = true;
		sz->x0 = (int)floorf((m.x - cam.offset.x) / cam.zoom);
		sz->y0 = (int)floorf((m.y - cam.offset.y) / cam.zoom);
		sz->x1 = sz->x0;
		sz->y1 = sz->y0;
	}
	if (sz->dragging && IsMouseButtonDown(MOUSE_BUTTON_LEFT))
	{
		sz->x1 = (int)floorf((m.x - cam.offset.x) / cam.zoom);
		sz->y1 = (int)floorf((m.y - cam.offset.y) / cam.zoom);
	}
	if (sz->dragging && IsMouseButtonReleased(MOUSE_BUTTON_LEFT))
	{
		sz->dragging = false;
		if (sz->x0 > sz->x1)
		{
			t = sz->x0;
			sz->x0 = sz->x1;
			sz->x1 = t;
		}
		if (sz->y0 > sz->y1)
		{
			t = sz->y0;
			sz->y0 = sz->y1;
			sz->y1 = t;
		}
		if (sz->x1 - sz->x0 + 1 > 0 && sz->y1 - sz->y0 + 1 > 0)
			sz->phase = 1;
	}
}

void	sz_draw_empty(void)
{
	DrawRectangle(10, 50, 240, 50, (Color){14, 14, 22, 210});
	DrawRectangleLinesEx((Rectangle){10, 50, 240, 50}, 1.5f,
		(Color){127, 119, 221, 180});
	DrawText("Export RLE : 0 x 0", 18, 58, 15,
		(Color){200, 200, 255, 240});
	DrawText("Cellules : 0", 18, 78, 15, (Color){200, 200, 255, 240});
}

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

void	sz_draw_dragging(t_save_zone_state *sz, t_camera2d_gol cam)
{
	t_bbox	box;
	float	sx;
	float	sy;
	float	rw;
	float	rh2;
	char	info1[80];
	char	info2[80];

	box = sz_normalize_box(sz);
	sx = box.x0 * cam.zoom + cam.offset.x;
	sy = box.y0 * cam.zoom + cam.offset.y;
	rw = (box.x1 - box.x0 + 1) * cam.zoom;
	rh2 = (box.y1 - box.y0 + 1) * cam.zoom;
	DrawRectangle((int)sx, (int)sy, (int)rw, (int)rh2,
		(Color){221, 185, 60, 30});
	DrawRectangleLinesEx((Rectangle){sx, sy, rw, rh2}, 2.0f,
		(Color){221, 185, 60, 220});
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

void	sz_phase0_draw(t_save_zone_state *sz, t_camera2d_gol cam)
{
	if (!sz->dragging)
	{
		sz_draw_empty();
		return ;
	}
	sz_draw_dragging(sz, cam);
}
