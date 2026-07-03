/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   simulation.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:32:57 by le-glitch         #+#    #+#             */
/*   Updated: 2026/07/02 22:30:00 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "simulation.h"

static void	sim_fetch_nbrs(const t_chunk_map *map, int cx, int cy,
				t_chunk_nbrs *nb)
{
	int	dx;
	int	dy;

	dy = -1;
	while (dy <= 1)
	{
		dx = -1;
		while (dx <= 1)
		{
			nb->c[dy + 1][dx + 1] = map_get(map, cx + dx, cy + dy);
			dx++;
		}
		dy++;
	}
}

static t_chunk	*sim_write_cell(t_chunk_map *next, t_chunk *out, t_cell_pos p)
{
	if (!out)
		out = map_get_or_create(next, p.cx, p.cy);
	if (out)
		chunk_set(out, p.lx, p.ly, 1);
	return (out);
}

void	sim_step_chunk(t_chunk_map *map, t_chunk_map *next, int *todo, int i)
{
	t_chunk_nbrs	nb;
	t_chunk			*out;
	t_cell_pos		p;

	sim_fetch_nbrs(map, todo[i * 2], todo[i * 2 + 1], &nb);
	out = NULL;
	p.cx = todo[i * 2];
	p.cy = todo[i * 2 + 1];
	p.ly = 0;
	while (p.ly < CHUNK_SIZE)
	{
		p.lx = 0;
		while (p.lx < CHUNK_SIZE)
		{
			if (sim_cell_will_live(&nb, p.lx, p.ly))
				out = sim_write_cell(next, out, p);
			p.lx++;
		}
		p.ly++;
	}
}

void	sim_compute_next(t_chunk_map *map, t_chunk_map *next, int *todo,
			int todo_count)
{
	int	i;

	i = 0;
	while (i < todo_count)
	{
		sim_step_chunk(map, next, todo, i);
		i++;
	}
}

void	simulation_step(t_chunk_map *map)
{
	t_chunk_map	next;
	int			*todo;
	int			cap;
	int			todo_count;

	if (map->chunk_count == 0)
		return ;
	cap = map->chunk_count * 9 + 16;
	if (cap > MAP_SIZE * 9)
		cap = MAP_SIZE * 9;
	todo = (int *)malloc((size_t)cap * 2 * sizeof(int));
	if (!todo)
		return ;
	todo_count = sim_collect_todo(map, todo, cap);
	if (todo_count < 0)
	{
		free(todo);
		return ;
	}
	map_init(&next);
	sim_compute_next(map, &next, todo, todo_count);
	free(todo);
	map_free(map);
	*map = next;
	map_remove_dead(map);
}
