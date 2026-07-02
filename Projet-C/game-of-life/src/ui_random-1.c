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

static void	rand_draw_slider_bar(t_random_state *rs, t_slider_geom sg,
				Rectangle p)
{
	int		pos;
	char	dpct[16];
	char	preview[48];

	DrawRectangle(sg.slx, sg.sly, sg.slw, 4, ui_c_border());
	pos = (int)(rs->density * sg.slw);
	DrawRectangle(sg.slx, sg.sly, pos, 4, ui_c_hi());
	DrawCircle(sg.slx + pos, sg.sly + 2, 6, ui_c_hi());
	snprintf(dpct, sizeof(dpct), "%.0f%%", rs->density * 100);
	DrawText(dpct, sg.slx + sg.slw + 8, sg.sly - 3, FS, ui_c_hi());
	snprintf(preview, sizeof(preview), "~%d cellules vivantes",
		(int)((rs->x1 - rs->x0 + 1) * (rs->y1 - rs->y0 + 1) * rs->density));
	DrawText(preview, (int)p.x + 20, (int)p.y + 108, FS - 1, ui_c_dim());
}

void	rand_draw_slider(t_random_state *rs, Rectangle p, int pw)
{
	t_slider_geom	sg;
	Rectangle		hit;

	sg.slx = (int)p.x + 90;
	sg.sly = (int)p.y + 88;
	sg.slw = pw - 140;
	rand_draw_slider_bar(rs, sg, p);
	hit = (Rectangle){(float)sg.slx, (float)(p.y + 74), (float)sg.slw, 24};
	rand_slider_input(rs, hit, sg.slx, sg.slw);
}
