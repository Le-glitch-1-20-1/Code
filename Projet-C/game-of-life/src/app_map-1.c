/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_map-1.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:25:39 by le-glitch         #+#    #+#             */
/*   Updated: 2026/07/10 20:51:09 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	center_map_row(t_chunk_map *tmp, const t_chunk *c, int cx, int cy)
{
	int	lx;
	int	ly;

	ly = 0;
	while (ly < CHUNK_SIZE)
	{
		if (c->cells[ly])
		{
			lx = 0;
			while (lx < CHUNK_SIZE)
			{
				if (chunk_get(c, lx, ly))
					set_cell_global(tmp,
						c->cx * CHUNK_SIZE + lx - cx,
						c->cy * CHUNK_SIZE + ly - cy, 1);
				lx++;
			}
		}
		ly++;
	}
}

void	center_map_iter(t_chunk_map *m, t_chunk_map *tmp, int cx, int cy)
{
	t_chunk	*n;
	int		bi;

	bi = 0;
	n = map_first(m, &bi);
	while (n)
	{
		center_map_row(tmp, n, cx, cy);
		n = map_next(m, &bi, n);
	}
}

void	center_map(t_chunk_map *m)
{
	t_chunk_map	tmp;
	t_bbox		box;
	int			cx;
	int			cy;

	map_bounding_box(m, &box);
	if (box.x0 > box.x1)
		return ;
	cx = get_center(box.x0, box.x1);
	cy = get_center(box.y0, box.y1);
	if (cx == 0 && cy == 0)
		return ;
	map_init(&tmp);
	center_map_iter(m, &tmp, cx, cy);
	map_free(m);
	*m = tmp;
}

int	get_center(int a, int b)
{
	return ((a + b) / 2);
}
