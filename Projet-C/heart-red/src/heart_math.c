/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   heart_math.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: you <you@student.42.fr>                   +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 00:00:00 by you               #+#    #+#             */
/*   Updated: 2026/09/02 00:00:00 by you              ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "heart.h"

void	heart_point(float t, float *x, float *y)
{
	*x = powf(sinf(t), 3);
	*y = -(13 * cosf(t) - 5 * cosf(2 * t)
			- 2 * cosf(3 * t) - cosf(4 * t)) / 16;
}

static void	update_bounds(t_bounds *b, float x, float y)
{
	if (x < b->minx)
		b->minx = x;
	if (x > b->maxx)
		b->maxx = x;
	if (y < b->miny)
		b->miny = y;
	if (y > b->maxy)
		b->maxy = y;
}

void	compute_heart_bounds(float *offx, float *offy)
{
	t_bounds	b;
	float		t;
	float		x;
	float		y;
	int			i;

	b.minx = 1e9f;
	b.maxx = -1e9f;
	b.miny = 1e9f;
	b.maxy = -1e9f;
	i = 0;
	while (i <= HEART_RESOLUTION)
	{
		t = (2 * PI * i) / HEART_RESOLUTION;
		heart_point(t, &x, &y);
		update_bounds(&b, x, y);
		i++;
	}
	*offx = (b.minx + b.maxx) / 2.0f;
	*offy = (b.miny + b.maxy) / 2.0f;
}
