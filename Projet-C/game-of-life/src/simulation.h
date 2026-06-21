/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   simulation.h                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:08:33 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:19:50 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef SIMULATION_H
# define SIMULATION_H

# include "chunk_map.h"
# include <stdlib.h>
# include <string.h>

static inline int	count_neighbors(const t_chunk_map *m, int gx, int gy)
{
	int	n;

	n = 0;
	n += get_cell_global(m, gx - 1, gy - 1);
	n += get_cell_global(m, gx, gy - 1);
	n += get_cell_global(m, gx + 1, gy - 1);
	n += get_cell_global(m, gx - 1, gy);
	n += get_cell_global(m, gx + 1, gy);
	n += get_cell_global(m, gx - 1, gy + 1);
	n += get_cell_global(m, gx, gy + 1);
	n += get_cell_global(m, gx + 1, gy + 1);
	return (n);
}

static inline int	sim_collect_dedup(unsigned int *seen, unsigned int set_mask,
	int ncx, int ncy)
{
	unsigned int		key;
	unsigned int		stored;
	unsigned int		slot;

	key = (unsigned int)((ncx + 0x8000) << 16
			| (unsigned int)((ncy + 0x8000) & 0xFFFF));
	stored = key + 1;
	slot = ((unsigned int)(ncx * 1000003u)
			^ (unsigned int)((unsigned int)ncy * 999983u)) & set_mask;
	while (seen[slot] != 0 && seen[slot] != stored)
		slot = (slot + 1) & set_mask;
	if (seen[slot] == 0)
	{
		seen[slot] = stored;
		return (1);
	}
	return (0);
}

static inline void	sim_visit_neighbors(t_chunk_node *node,
	unsigned int *seen, unsigned int smask,
	int *todo, int *todo_count, int cap)
{
	int	dx;
	int	dy;
	int	ncx;
	int	ncy;

	dx = -1;
	while (dx <= 1)
	{
		dy = -1;
		while (dy <= 1)
		{
			ncx = node->chunk.cx + dx;
			ncy = node->chunk.cy + dy;
			if (sim_collect_dedup(seen, smask, ncx, ncy)
				&& *todo_count < cap)
			{
				todo[*todo_count * 2] = ncx;
				todo[*todo_count * 2 + 1] = ncy;
				(*todo_count)++;
			}
			dy++;
		}
		dx++;
	}
}

static inline int	sim_collect_todo(t_chunk_map *map, int *todo, int cap)
{
	t_chunk_node	*node;
	unsigned int	*seen;
	int				todo_count;
	int				set_size;
	int				bucket_idx;

	set_size = 1;
	while (set_size < cap * 2)
		set_size <<= 1;
	seen = (unsigned int *)calloc((size_t)set_size, sizeof(unsigned int));
	if (!seen)
		return (-1);
	todo_count = 0;
	node = map_first(map, &bucket_idx);
	while (node)
	{
		sim_visit_neighbors(node, seen, (unsigned int)(set_size - 1),
			todo, &todo_count, cap);
		node = map_next(map, &bucket_idx, node);
	}
	free(seen);
	return (todo_count);
}

void	simulation_step(t_chunk_map *map);

#endif
