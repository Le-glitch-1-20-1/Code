/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_map-3.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:25:39 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 11:17:43 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	rotate_chunk(t_chunk_map *dst, const t_chunk *c)
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
	t_chunk	*n;
	int		bi;

	map_init(dst);
	bi = 0;
	n = map_first((t_chunk_map *)src, &bi);
	while (n)
	{
		rotate_chunk(dst, n);
		n = map_next((t_chunk_map *)src, &bi, n);
	}
}
