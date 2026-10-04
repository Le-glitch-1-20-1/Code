/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   heart_math.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: replace_me <replace_me@student.42.fr>     +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 00:00:00 by replace_me        #+#    #+#             */
/*   Updated: 2026/09/02 00:00:00 by replace_me       ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "heart.h"

void	heart_point(float t, float *x, float *y)
{
	*x = powf(sinf(t), 3);
	*y = -(13 * cosf(t) - 5 * cosf(2 * t) - 2 * cosf(3 * t)
			- cosf(4 * t)) / 16;
}

void	get_bounds(t_bounds *b)
{
	float	t;
	float	x;
	float	y;
	int		i;

	b->minx = 1e9f;
	b->maxx = -1e9f;
	b->miny = 1e9f;
	b->maxy = -1e9f;
	i = 0;
	while (i <= RESOL)
	{
		t = (2 * PI * i) / RESOL;
		heart_point(t, &x, &y);
		if (x < b->minx)
			b->minx = x;
		if (x > b->maxx)
			b->maxx = x;
		if (y < b->miny)
			b->miny = y;
		if (y > b->maxy)
			b->maxy = y;
		i++;
	}
}

void	build_points(Vector2 *points, t_heart_params *p,
			float offx, float offy)
{
	float	t;
	float	x;
	float	y;
	int		i;

	i = 0;
	while (i <= RESOL)
	{
		t = (2 * PI * i) / RESOL;
		heart_point(t, &x, &y);
		points[i].x = p->cx + p->scale * (x - offx);
		points[i].y = p->cy + p->scale * (y - offy);
		i++;
	}
}
