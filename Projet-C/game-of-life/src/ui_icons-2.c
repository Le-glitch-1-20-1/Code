/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_icons2.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:32:31 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/17 07:32:32 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"
#include "ui_shared.h"
#include "ui_icons.h"

void	icon_save(float cx, float cy, float r, Color c)
{
	int	x;
	int	y;
	int	s;

	x = (int)(cx - r * 0.75f);
	y = (int)(cy - r * 0.75f);
	s = (int)(r * 1.5f);
	DrawRectangle(x, y, s, s, c);
	DrawRectangle((int)(cx + r * 0.1f), y, (int)(r * 0.65f),
		(int)(r * 0.55f), C_PANEL2);
	DrawRectangle(x + 2, (int)(cy + r * 0.1f), s - 4,
		(int)(r * 0.65f), C_PANEL2);
}

void	icon_load(float cx, float cy, float r, Color c)
{
	Vector2	arr[3];

	DrawRectangle((int)(cx - r * 0.8f), (int)(cy - r * 0.3f),
		(int)(r * 1.6f), (int)(r * 1.1f), c);
	DrawRectangle((int)(cx - r * 0.8f), (int)(cy - r * 0.75f),
		(int)(r * 0.8f), (int)(r * 0.5f), c);
	DrawLineEx((Vector2){cx, cy - r * 0.05f},
		(Vector2){cx, cy + r * 0.6f}, r * 0.3f, C_PANEL2);
	arr[0] = (Vector2){cx - r * 0.45f, cy + r * 0.3f};
	arr[1] = (Vector2){cx + r * 0.45f, cy + r * 0.3f};
	arr[2] = (Vector2){cx, cy + r * 0.7f};
	DrawTriangle(arr[0], arr[1], arr[2], C_PANEL2);
}

void	icon_random(float cx, float cy, float r, Color c)
{
	int	dx;
	int	dy;

	dy = -1;
	while (dy <= 1)
	{
		dx = -1;
		while (dx <= 1)
		{
			if ((dx + dy + 2) % 2 == 0)
				DrawRectangle(
					(int)(cx + dx * r * 0.55f - r * 0.18f),
					(int)(cy + dy * r * 0.55f - r * 0.18f),
					(int)(r * 0.36f), (int)(r * 0.36f), c);
			dx++;
		}
		dy++;
	}
}

void	icon_menu(float cx, float cy, float r, Color c)
{
	int	bh;
	int	bw;
	int	bx;

	bh = (int)(r * 0.22f);
	bw = (int)(r * 1.5f);
	bx = (int)(cx - r * 0.75f);
	DrawRectangle(bx, (int)(cy - r * 0.6f), bw, bh, c);
	DrawRectangle(bx, (int)(cy - r * 0.1f), bw, bh, c);
	DrawRectangle(bx, (int)(cy + r * 0.4f), bw, bh, c);
}

void	icon_grid(float cx, float cy, float r, Color c)
{
	float	s;
	int		dx;
	int		dy;

	s = r * 0.42f;
	dy = -1;
	while (dy <= 1)
	{
		dx = -1;
		while (dx <= 1)
		{
			DrawRectangleLinesEx((Rectangle){
				cx + dx * r * 0.65f - s / 2,
				cy + dy * r * 0.65f - s / 2, s, s}, 1.0f, c);
			dx++;
		}
		dy++;
	}
}
