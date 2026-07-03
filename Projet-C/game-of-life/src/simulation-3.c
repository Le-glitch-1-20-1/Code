/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   simulation-3.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/02 22:30:00 by le-glitch         #+#    #+#             */
/*   Updated: 2026/07/02 22:30:00 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "simulation.h"

static int	sim_local_get(t_chunk_nbrs *nb, int lx, int ly)
{
	const t_chunk	*c;
	int				bx;
	int				by;

	bx = 1;
	by = 1;
	if (lx < 0)
	{
		lx += CHUNK_SIZE;
		bx = 0;
	}
	else if (lx >= CHUNK_SIZE)
	{
		lx -= CHUNK_SIZE;
		bx = 2;
	}
	if (ly < 0)
	{
		ly += CHUNK_SIZE;
		by = 0;
	}
	else if (ly >= CHUNK_SIZE)
	{
		ly -= CHUNK_SIZE;
		by = 2;
	}
	c = nb->c[by][bx];
	if (!c)
		return (0);
	return (chunk_get(c, lx, ly));
}

static int	sim_local_neighbors(t_chunk_nbrs *nb, int lx, int ly)
{
	int	n;

	n = 0;
	n += sim_local_get(nb, lx - 1, ly - 1);
	n += sim_local_get(nb, lx, ly - 1);
	n += sim_local_get(nb, lx + 1, ly - 1);
	n += sim_local_get(nb, lx - 1, ly);
	n += sim_local_get(nb, lx + 1, ly);
	n += sim_local_get(nb, lx - 1, ly + 1);
	n += sim_local_get(nb, lx, ly + 1);
	n += sim_local_get(nb, lx + 1, ly + 1);
	return (n);
}

int	sim_cell_will_live(t_chunk_nbrs *nb, int lx, int ly)
{
	int	alive;
	int	n;

	alive = sim_local_get(nb, lx, ly);
	n = sim_local_neighbors(nb, lx, ly);
	if (alive)
		return (n == 2 || n == 3);
	return (n == 3);
}
