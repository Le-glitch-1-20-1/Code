/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_map-1.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:25:39 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 09:08:24 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

static void	center_map_iter(t_chunk_map *m, t_chunk_map *tmp, int cx, int cy)
{
	t_chunk_node	*n;
	const t_chunk	*c;
	int				bi;
	int				lx;
	int				ly;

	bi = 0;
	n = map_first(m, &bi);
	while (n)
	{
		c = &n->chunk;
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
		n = map_next(m, &bi, n);
	}
}

static int	get_center(int a, int b)
{
	return ((a + b) / 2);
}

void	center_map(t_chunk_map *m)
{
	t_chunk_map	tmp;
	int			bbox[4];
	int			cx;
	int			cy;

	map_bounding_box(m, &bbox[0], &bbox[1], &bbox[2], &bbox[3]);
	if (bbox[0] > bbox[2])
		return ;
	cx = get_center(bbox[0], bbox[2]);
	cy = get_center(bbox[1], bbox[3]);
	if (cx == 0 && cy == 0)
		return ;
	map_init(&tmp);
	center_map_iter(m, &tmp, cx, cy);
	map_free(m);
	*m = tmp;
}

static void	rotate_chunk(t_chunk_map *dst, const t_chunk *c)
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
					set_cell_global(dst,
						c->cy * CHUNK_SIZE + ly,
						-(c->cx * CHUNK_SIZE + lx), 1);
				lx++;
			}
		}
		ly++;
	}
}

void	rotate_map_90(const t_chunk_map *src, t_chunk_map *dst)
{
	t_chunk_node	*n;
	int				bi;

	map_init(dst);
	bi = 0;
	n = map_first((t_chunk_map *)src, &bi);
	while (n)
	{
		rotate_chunk(dst, &n->chunk);
		n = map_next((t_chunk_map *)src, &bi, n);
	}
}
