/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_icons-3.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:10:04 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:19:56 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"
#include "ui_shared.h"
#include "ui_icons.h"

void	icon_hud(float cx, float cy, float r, Color c)
{
	int	bw;
	int	bh2;

	bw = (int)(r * 1.5f);
	bh2 = (int)(r * 0.3f);
	DrawRectangle((int)(cx - r * 0.75f), (int)(cy + r * 0.6f), bw, bh2, c);
	DrawRectangle((int)(cx - r * 0.75f), (int)(cy - r * 0.8f), bw, bh2, c);
	DrawRectangle((int)(cx - r * 0.75f), (int)(cy - r * 0.2f),
		(int)(r * 0.9f), bh2, c);
}

void	icon_chunk_debug(float cx, float cy, float r, Color c)
{
	float	s;
	int		dx;
	int		dy;

	s = r * 0.65f;
	dy = -1;
	while (dy <= 1)
	{
		dx = -1;
		while (dx <= 1)
		{
			DrawRectangleLinesEx((Rectangle){
				cx + dx * r * 0.4f - s / 2,
				cy + dy * r * 0.4f - s / 2, s, s}, 1.5f, c);
			dx += 2;
		}
		dy += 2;
	}
}

void	icon_undo(float cx, float cy, float r, Color c)
{
	Vector2	tip[3];

	DrawCircleLines((int)cx, (int)cy, (int)(r * 0.75f), c);
	DrawRectangle((int)(cx - r * 0.1f), (int)(cy - r * 0.85f),
		(int)(r * 0.75f), (int)(r * 0.75f), C_PANEL);
	tip[0] = (Vector2){cx - r * 0.85f, cy - r * 0.25f};
	tip[1] = (Vector2){cx - r * 0.35f, cy - r * 0.8f};
	tip[2] = (Vector2){cx - r * 0.35f, cy + r * 0.3f};
	DrawTriangle(tip[0], tip[1], tip[2], c);
}

void	icon_copy(float cx, float cy, float r, Color c)
{
	int	sw2;
	int	sh2;

	sw2 = (int)(r * 1.0f);
	sh2 = (int)(r * 1.1f);
	DrawRectangleLinesEx((Rectangle){cx - r * 0.6f, cy - r * 0.8f,
		sw2, sh2}, 1.5f, c);
	DrawRectangleLinesEx((Rectangle){cx - r * 0.2f, cy - r * 0.4f,
		sw2, sh2}, 1.5f, c);
}

void	icon_clear_zone(float cx, float cy, float r, Color c)
{
	float	s;

	s = r * 1.4f;
	DrawRectangleLinesEx((Rectangle){cx - s / 2, cy - s / 2, s, s},
		1.5f, c);
	DrawLineEx((Vector2){cx - r * 0.4f, cy - r * 0.4f},
		(Vector2){cx + r * 0.4f, cy + r * 0.4f}, 1.5f, c);
	DrawLineEx((Vector2){cx + r * 0.4f, cy - r * 0.4f},
		(Vector2){cx - r * 0.4f, cy + r * 0.4f}, 1.5f, c);
}
