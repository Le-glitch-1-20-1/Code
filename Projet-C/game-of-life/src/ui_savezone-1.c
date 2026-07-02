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

static void	sz_swap_coords(t_save_zone_state *sz)
{
	int	t;

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

void	sz_phase0_input(t_save_zone_state *sz, t_camera2d_gol cam)
{
	Vector2	m;
	bool	on_ui;

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
		sz_swap_coords(sz);
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
