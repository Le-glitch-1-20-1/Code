/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_hud.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:28:19 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/17 07:28:20 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"
#include "ui_shared.h"

static void	hud_graph_loop(const int *pop, int start,
	int n, int gx2, int gy2, int gh, float bar_w, int pm)
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
		bar_h = (int)((float)v / pm * (gh - 2));
		if (bar_h < 1 && v > 0)
			bar_h = 1;
		intensity = (unsigned char)(100 + 120 * v / pm);
		if (bar_w > 1)
			bw = bar_w - 0.5f;
		else
			bw = bar_w;
		DrawRectangleRec(
			(Rectangle){gx2 + i * bar_w, gy2 + gh - 1 - bar_h,
				bw, (float)bar_h},
			(Color){intensity / 2, intensity / 3, intensity, 200});
		i++;
	}
}

static void	hud_draw_graph(int x, int by, int bh,
	const int *pop_history, int pop_count, int pop_max)
{
	int		gw;
	int		gh;
	int		start;
	int		n;
	float	bar_w;

	gw = 140;
	gh = bh - 6;
	DrawRectangle(x, by + 3, gw, gh, (Color){18, 18, 28, 200});
	DrawRectangleLinesEx((Rectangle){x, by + 3, gw, gh}, 1.0f, C_BORDER);
	if (pop_count > gw)
		start = pop_count - gw;
	else
		start = 0;
	n = pop_count - start;
	bar_w = (float)gw / n;
	hud_graph_loop(pop_history, start, n, x, by + 3, gh, bar_w, pop_max);
	DrawText("pop", x + 2, by + 4, 10, C_DIM);
}

static void	hud_draw_status(bool running, int x, int y)
{
	if (running)
		DrawText("[RUN]", x, y, FS, C_GREEN);
	else
		DrawText("[PAU]", x, y, FS, C_YELLOW);
}

static void	hud_draw_text(int generation, float speed, int alive_count,
	int gx, int gy, int by)
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

void	ui_draw_hud(int generation, bool running, float speed, int alive_count,
	int gx, int gy, const int *pop_history, int pop_count, int pop_max)
{
	int	sw;
	int	sh;
	int	bh;
	int	by;
	int	x;

	sw = GetScreenWidth();
	sh = GetScreenHeight();
	bh = 26;
	by = sh - bh;
	DrawRectangle(0, by, sw, bh, C_PANEL);
	DrawLine(0, by, sw, by, C_BORDER);
	x = 10;
	hud_draw_status(running, x, by + (bh - FS) / 2);
	hud_draw_text(generation, speed, alive_count, gx, gy, by);
	x = 10 + 70 + 130 + 150 + 90 + 90 + 120;
	if (pop_count > 1 && pop_max > 0)
		hud_draw_graph(x, by, bh, pop_history, pop_count, pop_max);
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
