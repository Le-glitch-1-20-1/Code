/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_input-7.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:30:44 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 07:26:03 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"
#include "simulation.h"

#include "main.h"

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

void	draw_line_cells(t_chunk_map *map, int x0, int y0,
	int x1, int y1, int val)
{
	int	dx;
	int	dy;
	int	sx;
	int	sy;
	int	err;
	int	e2;

	dx = abs(x1 - x0);
	sx = bresenham_sx(x0, x1);
	dy = -abs(y1 - y0);
	sy = bresenham_sy(y0, y1);
	err = dx + dy;
	while (1)
	{
		set_cell_global(map, x0, y0, val);
		if (x0 == x1 && y0 == y1)
			break ;
		e2 = 2 * err;
		if (e2 >= dy)
		{
			err += dy;
			x0 += sx;
		}
		if (e2 <= dx)
		{
			err += dx;
			y0 += sy;
		}
	}
}
