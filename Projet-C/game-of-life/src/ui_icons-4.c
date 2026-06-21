/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_icons-4.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:37:54 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:19:58 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"
#include "ui_shared.h"
#include "ui_icons.h"

void	icon_play(float cx, float cy, float r, Color c)
{
	Vector2	pts[3];

	pts[0] = (Vector2){cx - r * 0.6f, cy - r * 0.8f};
	pts[1] = (Vector2){cx - r * 0.6f, cy + r * 0.8f};
	pts[2] = (Vector2){cx + r * 0.8f, cy};
	DrawTriangle(pts[0], pts[1], pts[2], c);
}

void	icon_pause(float cx, float cy, float r, Color c)
{
	int	bw;
	int	bh;

	bw = (int)(r * 0.4f);
	bh = (int)(r * 1.6f);
	DrawRectangle((int)(cx - r * 0.7f), (int)(cy - r * 0.8f), bw, bh, c);
	DrawRectangle((int)(cx + r * 0.3f), (int)(cy - r * 0.8f), bw, bh, c);
}

void	icon_step(float cx, float cy, float r, Color c)
{
	Vector2	pts[3];

	pts[0] = (Vector2){cx - r * 0.6f, cy - r * 0.8f};
	pts[1] = (Vector2){cx - r * 0.6f, cy + r * 0.8f};
	pts[2] = (Vector2){cx + r * 0.4f, cy};
	DrawTriangle(pts[0], pts[1], pts[2], c);
	DrawRectangle((int)(cx + r * 0.5f), (int)(cy - r * 0.8f),
		(int)(r * 0.35f), (int)(r * 1.6f), c);
}

void	icon_clear(float cx, float cy, float r, Color c)
{
	float	t;

	t = r * 0.18f;
	DrawLineEx((Vector2){cx - r * 0.7f, cy - r * 0.7f},
		(Vector2){cx + r * 0.7f, cy + r * 0.7f}, t * 2, c);
	DrawLineEx((Vector2){cx + r * 0.7f, cy - r * 0.7f},
		(Vector2){cx - r * 0.7f, cy + r * 0.7f}, t * 2, c);
}
