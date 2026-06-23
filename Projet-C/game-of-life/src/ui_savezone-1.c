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

void	sz_draw_dragging(t_save_zone_state *sz, t_camera2d_gol cam)
{
	int		xa;
	int		ya;
	int		xb;
	int		yb;
	int		t;
	float	sx;
	float	sy;
	float	rw;
	float	rh2;
	char	info1[80];
	char	info2[80];

	xa = sz->x0;
	ya = sz->y0;
	xb = sz->x1;
	yb = sz->y1;
	if (xa > xb)
	{
		t = xa;
		xa = xb;
		xb = t;
	}
	if (ya > yb)
	{
		t = ya;
		ya = yb;
		yb = t;
	}
	sx = xa * cam.zoom + cam.offset.x;
	sy = ya * cam.zoom + cam.offset.y;
	rw = (xb - xa + 1) * cam.zoom;
	rh2 = (yb - ya + 1) * cam.zoom;
	DrawRectangle((int)sx, (int)sy, (int)rw, (int)rh2,
		(Color){221, 185, 60, 30});
	DrawRectangleLinesEx((Rectangle){sx, sy, rw, rh2}, 2.0f,
		(Color){221, 185, 60, 220});
	snprintf(info1, sizeof(info1), "Export RLE : %d x %d",
		abs(xb - xa) + 1, abs(yb - ya) + 1);
	snprintf(info2, sizeof(info2), "Cellules : %d",
		(abs(xb - xa) + 1) * (abs(yb - ya) + 1));
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

int	is_valid_name_char(int k)
{
	if ((k >= 'a' && k <= 'z') || (k >= 'A' && k <= 'Z'))
		return (1);
	if ((k >= '0' && k <= '9') || k == '_' || k == '-')
		return (1);
	return (0);
}

void	sz_name_edit(t_save_zone_state *sz)
{
	int	k;
	int	len;

	k = GetCharPressed();
	while (k > 0)
	{
		len = (int)strlen(sz->name_buf);
		if (is_valid_name_char(k) && len < 60)
		{
			sz->name_buf[len] = (char)k;
			sz->name_buf[len + 1] = 0;
		}
		k = GetCharPressed();
	}
	if (IsKeyPressed(KEY_BACKSPACE))
	{
		len = (int)strlen(sz->name_buf);
		if (len > 0)
			sz->name_buf[len - 1] = 0;
	}
}
