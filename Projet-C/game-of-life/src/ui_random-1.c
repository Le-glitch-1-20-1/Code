/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_random.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:06:23 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 22:47:01 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

void	rand_swap_coords(t_random_state *rs)
{
	int	t;

	if (rs->x0 > rs->x1)
	{
		t = rs->x0;
		rs->x0 = rs->x1;
		rs->x1 = t;
	}
	if (rs->y0 > rs->y1)
	{
		t = rs->y0;
		rs->y0 = rs->y1;
		rs->y1 = t;
	}
	if (rs->x1 - rs->x0 + 1 > 1 && rs->y1 - rs->y0 + 1 > 1)
		rs->phase = 1;
}

void	rand_phase0(t_random_state *rs, t_camera2d_gol cam)
{
	Vector2	m;
	bool	on_ui;

	m = GetMousePosition();
	on_ui = (m.y < 42);
	if (!on_ui && IsMouseButtonPressed(MOUSE_BUTTON_LEFT))
	{
		rs->dragging = true;
		rs->x0 = (int)floorf((m.x - cam.offset.x) / cam.zoom);
		rs->y0 = (int)floorf((m.y - cam.offset.y) / cam.zoom);
		rs->x1 = rs->x0;
		rs->y1 = rs->y0;
	}
	if (rs->dragging && IsMouseButtonDown(MOUSE_BUTTON_LEFT))
	{
		rs->x1 = (int)floorf((m.x - cam.offset.x) / cam.zoom);
		rs->y1 = (int)floorf((m.y - cam.offset.y) / cam.zoom);
	}
	if (rs->dragging && IsMouseButtonReleased(MOUSE_BUTTON_LEFT))
	{
		rs->dragging = false;
		rand_swap_coords(rs);
	}
	if (IsKeyPressed(KEY_ESCAPE))
		rs->cancelled = true;
}

void	rand_slider_input(t_random_state *rs, Rectangle hit, int slx, int slw)
{
	float	nt;

	if (!CheckCollisionPointRec(GetMousePosition(), hit)
		|| !IsMouseButtonDown(0))
		return ;
	nt = (GetMousePosition().x - slx) / slw;
	if (nt < 0)
		nt = 0;
	if (nt > 1)
		nt = 1;
	rs->density = nt;
}

static void	rand_draw_slider_bar(t_random_state *rs, int slx, int sly,
				int slw, Rectangle p)
{
	int		pos;
	char	dpct[16];
	char	preview[48];

	DrawRectangle(slx, sly, slw, 4, C_BORDER);
	pos = (int)(rs->density * slw);
	DrawRectangle(slx, sly, pos, 4, C_HI);
	DrawCircle(slx + pos, sly + 2, 6, C_HI);
	snprintf(dpct, sizeof(dpct), "%.0f%%", rs->density * 100);
	DrawText(dpct, slx + slw + 8, sly - 3, FS, C_HI);
	snprintf(preview, sizeof(preview), "~%d cellules vivantes",
		(int)((rs->x1 - rs->x0 + 1) * (rs->y1 - rs->y0 + 1) * rs->density));
	DrawText(preview, (int)p.x + 20, (int)p.y + 108, FS - 1, C_DIM);
}

void	rand_draw_slider(t_random_state *rs, Rectangle p, int pw)
{
	int			slx;
	int			sly;
	int			slw;
	Rectangle	hit;

	slx = (int)p.x + 90;
	sly = (int)p.y + 88;
	slw = pw - 140;
	rand_draw_slider_bar(rs, slx, sly, slw, p);
	hit = (Rectangle){(float)slx, (float)(p.y + 74), (float)slw, 24};
	rand_slider_input(rs, hit, slx, slw);
}
