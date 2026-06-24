/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   simulation_collect.c                               :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:08:33 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 11:21:27 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "simulation.h"

int	count_neighbors(const t_chunk_map *m, int gx, int gy)
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

int	sim_collect_dedup(unsigned int *seen, unsigned int set_mask, int ncx,
		int ncy)
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

void	sim_visit_neighbors(t_chunk *node, t_dedup_ctx *dedup,
			t_todo_ctx *todo)
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
			ncx = node->cx + dx;
			ncy = node->cy + dy;
			if (sim_collect_dedup(dedup->seen, dedup->smask, ncx, ncy)
				&& *(todo->todo_count) < todo->cap)
			{
				todo->todo[*(todo->todo_count) * 2] = ncx;
				todo->todo[*(todo->todo_count) * 2 + 1] = ncy;
				(*(todo->todo_count))++;
			}
			dy++;
		}
		dx++;
	}
}

t_dedup_ctx	sim_init_dedup(int cap)
{
	t_dedup_ctx	dedup;
	int			set_size;

	set_size = 1;
	while (set_size < cap * 2)
		set_size <<= 1;
	dedup.seen = (unsigned int *)calloc((size_t)set_size,
			sizeof(unsigned int));
	dedup.smask = (unsigned int)(set_size - 1);
	return (dedup);
}

int	sim_collect_todo(t_chunk_map *map, int *todo, int cap)
{
	t_chunk			*node;
	t_dedup_ctx		dedup;
	t_todo_ctx		tctx;
	int				todo_count;
	int				bucket_idx;

	dedup = sim_init_dedup(cap);
	if (!dedup.seen)
		return (-1);
	todo_count = 0;
	tctx.todo = todo;
	tctx.todo_count = &todo_count;
	tctx.cap = cap;
	node = map_first(map, &bucket_idx);
	while (node)
	{
		sim_visit_neighbors(node, &dedup, &tctx);
		node = map_next(map, &bucket_idx, node);
	}
	free(dedup.seen);
	return (todo_count);
}
