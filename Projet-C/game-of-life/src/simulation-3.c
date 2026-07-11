/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   simulation-3.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/02 22:30:00 by le-glitch         #+#    #+#             */
/*   Updated: 2026/07/10 22:04:32 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "simulation.h"

void	sim_wrap_axis(int *lc, int *bc)
{
	*bc = 1;
	if (*lc < 0)
	{
		*lc += CHUNK_SIZE;
		*bc = 0;
	}
	else if (*lc >= CHUNK_SIZE)
	{
		*lc -= CHUNK_SIZE;
		*bc = 2;
	}
}

int	sim_local_get(t_chunk_nbrs *nb, int lx, int ly)
{
	const t_chunk	*c;
	int				bx;
	int				by;

	sim_wrap_axis(&lx, &bx);
	sim_wrap_axis(&ly, &by);
	c = nb->c[by][bx];
	if (!c)
		return (0);
	return (chunk_get(c, lx, ly));
}

int	sim_local_neighbors(t_chunk_nbrs *nb, int lx, int ly)
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
