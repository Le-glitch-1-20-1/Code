/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_hud.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:07:15 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 22:26:01 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

void	hud_graph_loop(const int *pop, int start, int n, t_graph_geom g)
{
	int				i;
	int				v;
	int				bar_h;
	unsigned char	intensity;
	float			bw;

	i = 0;
	while (i < n)
	{
		v = pop[start + i];
		bar_h = (int)((float)v / g.pm * (g.gh - 2));
		if (bar_h < 1 && v > 0)
			bar_h = 1;
		intensity = (unsigned char)(100 + 120 * v / g.pm);
		if (g.bar_w > 1)
			bw = g.bar_w - 0.5f;
		else
			bw = g.bar_w;
		DrawRectangleRec(
			(Rectangle){g.gx + i * g.bar_w, g.gy + g.gh - 1 - bar_h,
			bw, (float)bar_h},
			(Color){intensity / 2, intensity / 3, intensity, 200});
		i++;
	}
}

void	hud_draw_graph(int x, int by, int bh, t_hud_info h)
{
	int				gw;
	int				gh;
	int				start;
	int				n;
	t_graph_geom	g;

	gw = 140;
	gh = bh - 6;
	DrawRectangle(x, by + 3, gw, gh, (Color){18, 18, 28, 200});
	DrawRectangleLinesEx((Rectangle){x, by + 3, gw, gh}, 1.0f, ui_c_border());
	if (h.pop_count > gw)
		start = h.pop_count - gw;
	else
		start = 0;
	n = h.pop_count - start;
	g = (t_graph_geom){x, by + 3, gh, (float)gw / n, h.pop_max};
	hud_graph_loop(h.pop_history, start, n, g);
	DrawText("pop", x + 2, by + 4, 10, ui_c_dim());
}

void	hud_draw_status(bool running, int x, int y)
{
	if (running)
		DrawText("[RUN]", x, y, FS, ui_c_green());
	else
		DrawText("[PAU]", x, y, FS, ui_c_yellow());
}

void	hud_draw_text(t_hud_info h, int by)
{
	int		bh;
	int		x;
	int		y;
	char	buf[64];

	bh = 26;
	x = 10;
	y = by + (bh - FS) / 2;
	x += 70;
	snprintf(buf, sizeof(buf), "Gen:%d", h.generation);
	DrawText(buf, x, y, FS, ui_c_text());
	x += 130;
	snprintf(buf, sizeof(buf), "%d cellules", h.alive_count);
	DrawText(buf, x, y, FS, ui_c_text());
	x += 150;
	snprintf(buf, sizeof(buf), "%.0f g/s", h.speed);
	DrawText(buf, x, y, FS, ui_c_hi());
	x += 90;
	snprintf(buf, sizeof(buf), "%d FPS", GetFPS());
	DrawText(buf, x, y, FS, ui_c_dim());
	x += 90;
	snprintf(buf, sizeof(buf), "(%d, %d)", h.gx, h.gy);
	DrawText(buf, x, y, FS, ui_c_dim());
}

void	ui_draw_hud(t_hud_info h)
{
	int	sw;
	int	sh;
	int	bh;
	int	by;

	sw = GetScreenWidth();
	sh = GetScreenHeight();
	bh = 26;
	by = sh - bh;
	DrawRectangle(0, by, sw, bh, ui_c_panel());
	DrawLine(0, by, sw, by, ui_c_border());
	hud_draw_status(h.running, 10, by + (bh - FS) / 2);
	hud_draw_text(h, by);
	if (h.pop_count > 1 && h.pop_max > 0)
		hud_draw_graph(10 + 70 + 130 + 150 + 90 + 90 + 120, by, bh, h);
}
