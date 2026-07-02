/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_input-7.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:30:44 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 22:01:12 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

int	bresenham_sx(int x0, int x1)
{
	if (x0 < x1)
		return (1);
	return (-1);
}

int	bresenham_sy(int y0, int y1)
{
	if (y0 < y1)
		return (1);
	return (-1);
}

static void	bresenham_step(int *x0, int *y0, t_bresenham *b)
{
	int	e2;

	e2 = 2 * b->err;
	if (e2 >= b->dy)
	{
		b->err += b->dy;
		*x0 += b->sx;
	}
	if (e2 <= b->dx)
	{
		b->err += b->dx;
		*y0 += b->sy;
	}
}

void	draw_line_cells(t_chunk_map *map, t_rect r, int val)
{
	t_bresenham	b;
	int			x0;
	int			y0;

	x0 = r.xa;
	y0 = r.ya;
	b.dx = abs(r.xb - x0);
	b.sx = bresenham_sx(x0, r.xb);
	b.dy = -abs(r.yb - y0);
	b.sy = bresenham_sy(y0, r.yb);
	b.err = b.dx + b.dy;
	while (1)
	{
		set_cell_global(map, x0, y0, val);
		if (x0 == r.xb && y0 == r.yb)
			break ;
		bresenham_step(&x0, &y0, &b);
	}
}
