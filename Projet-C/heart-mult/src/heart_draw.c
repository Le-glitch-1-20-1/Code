/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   heart_draw.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 21:27:04 by le-glitch         #+#    #+#             */
/*   Updated: 2026/09/02 21:27:10 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "heart.h"

void	draw_glow(Vector2 *points, float time_offset, float thickness)
{
	float	hue;
	Color	col;
	int		i;

	i = 0;
	while (i < RESOL)
	{
		hue = fmodf(((float)i / RESOL) + time_offset, 1.0f) * 360.0f;
		col = ColorFromHSV(hue, 1.0f, 1.0f);
		DrawLineEx(points[i], points[i + 1], thickness + 4.0f,
			Fade(col, 0.25f));
		i++;
	}
}

void	draw_main_line(Vector2 *points, float time_offset, float thickness)
{
	float	hue;
	Color	col;
	int		i;

	i = 0;
	while (i < RESOL)
	{
		hue = fmodf(((float)i / RESOL) + time_offset, 1.0f) * 360.0f;
		col = ColorFromHSV(hue, 1.0f, 1.0f);
		DrawLineEx(points[i], points[i + 1], thickness, col);
		DrawCircleV(points[i], thickness / 2.0f, col);
		i++;
	}
}

void	draw_heart_outline(t_heart_params *p)
{
	Vector2		points[RESOL + 1];
	t_bounds	b;
	float		offx;
	float		offy;

	get_bounds(&b);
	offx = (b.minx + b.maxx) / 2.0f;
	offy = (b.miny + b.maxy) / 2.0f;
	build_points(points, p, offx, offy);
	draw_glow(points, p->time_offset, p->thickness);
	draw_main_line(points, p->time_offset, p->thickness);
}
