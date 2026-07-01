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

typedef struct s_graph_geom
{
	int		gx;
	int		gy;
	int		gh;
	float	bar_w;
	int		pm;
}	t_graph_geom;

void	hud_graph_loop(const int *pop, int start, int n, t_graph_geom g)
{
	int				i;
	int				v;
	int				bar_h;
	unsigned char	intensity;

	i = 0;
	while (i < n)
	{
		v = pop[start + i];
		bar_h = (int)((float)v / g.pm * (g.gh - 2));
		if (bar_h < 1 && v > 0)
			bar_h = 1;
		intensity = (unsigned char)(100 + 120 * v / g.pm);
		DrawRectangleRec(
			(Rectangle){g.gx + i * g.bar_w, g.gy + g.gh - 1 - bar_h,
			(g.bar_w > 1) ? g.bar_w - 0.5f : g.bar_w, (float)bar_h},
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
	DrawRectangleLinesEx((Rectangle){x, by + 3, gw, gh}, 1.0f, C_BORDER);
	if (h.pop_count > gw)
		start = h.pop_count - gw;
	else
		start = 0;
	n = h.pop_count - start;
	g = (t_graph_geom){x, by + 3, gh, (float)gw / n, h.pop_max};
	hud_graph_loop(h.pop_history, start, n, g);
	DrawText("pop", x + 2, by + 4, 10, C_DIM);
}

void	hud_draw_status(bool running, int x, int y)
{
	if (running)
		DrawText("[RUN]", x, y, FS, C_GREEN);
	else
		DrawText("[PAU]", x, y, FS, C_YELLOW);
}

void	hud_draw_text(int generation, float speed, int alive_count, int gx,
			int gy, int by)
{
	int		bh;
	int		x;
	int		y;
	char	buf[64];

	bh = 26;
	x = 10;
	y = by + (bh - FS) / 2;
	x += 70;
	snprintf(buf, sizeof(buf), "Gen:%d", generation);
	DrawText(buf, x, y, FS, C_TEXT);
	x += 130;
	snprintf(buf, sizeof(buf), "%d cellules", alive_count);
	DrawText(buf, x, y, FS, C_TEXT);
	x += 150;
	snprintf(buf, sizeof(buf), "%.0f g/s", speed);
	DrawText(buf, x, y, FS, C_HI);
	x += 90;
	snprintf(buf, sizeof(buf), "%d FPS", GetFPS());
	DrawText(buf, x, y, FS, C_DIM);
	x += 90;
	snprintf(buf, sizeof(buf), "(%d, %d)", gx, gy);
	DrawText(buf, x, y, FS, C_DIM);
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
	DrawRectangle(0, by, sw, bh, C_PANEL);
	DrawLine(0, by, sw, by, C_BORDER);
	hud_draw_status(h.running, 10, by + (bh - FS) / 2);
	hud_draw_text(h.generation, h.speed, h.alive_count, h.gx, h.gy, by);
	if (h.pop_count > 1 && h.pop_max > 0)
		hud_draw_graph(10 + 70 + 130 + 150 + 90 + 90 + 120, by, bh, h);
}

void	ui_draw_message(const char *msg, float timer)
{
	int		mw;
	int		top;
	float	a;

	if (timer <= 0.0f || !msg[0])
		return ;
	if (timer > 0.5f)
		a = 1.0f;
	else
		a = timer / 0.5f;
	mw = MeasureText(msg, FS) + 20;
	top = 44;
	DrawRectangle(10, top, mw, 26,
		(Color){0, 0, 0, (unsigned char)(a * 160)});
	DrawRectangleLinesEx((Rectangle){10, top, mw, 26}, 1.0f,
		(Color){127, 119, 221, (unsigned char)(a * 180)});
	DrawText(msg, 20, top + (26 - FS) / 2, FS,
		(Color){220, 220, 230, (unsigned char)(a * 240)});
}
