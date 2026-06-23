/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   simulation.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:32:57 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 11:07:30 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "simulation.h"

static void	sim_step_cell(t_chunk_map *map, t_chunk_map *next,
	int gx, int gy)
{
	int	alive;
	int	nb;
	int	ns;

	alive = get_cell_global(map, gx, gy);
	nb = count_neighbors(map, gx, gy);
	if (alive)
		ns = (nb == 2 || nb == 3);
	else
		ns = (nb == 3);
	if (ns)
		set_cell_global(next, gx, gy, 1);
}

static void	sim_step_chunk(t_chunk_map *map, t_chunk_map *next,
	int *todo, int i)
{
	int	lx;
	int	ly;
	int	gx;
	int	gy;

	ly = 0;
	while (ly < CHUNK_SIZE)
	{
		lx = 0;
		while (lx < CHUNK_SIZE)
		{
			gx = todo[i * 2] * CHUNK_SIZE + lx;
			gy = todo[i * 2 + 1] * CHUNK_SIZE + ly;
			sim_step_cell(map, next, gx, gy);
			lx++;
		}
		ly++;
	}
}

static void	sim_compute_next(t_chunk_map *map, t_chunk_map *next,
	int *todo, int todo_count)
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
