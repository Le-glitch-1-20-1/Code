/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   simulation.h                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:08:33 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 22:17:43 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef SIMULATION_H
# define SIMULATION_H

# include "main.h"
# include "chunk.h"

typedef struct s_dedup_ctx
{
	unsigned int	*seen;
	unsigned int	smask;
}	t_dedup_ctx;

typedef struct s_todo_ctx
{
	int	*todo;
	int	*todo_count;
	int	cap;
}	t_todo_ctx;

// simulation.c
void		sim_step_cell(t_chunk_map *map, t_chunk_map *next, int gx, int gy);
void		sim_step_chunk(t_chunk_map *map, t_chunk_map *next, int *todo,
				int i);
void		sim_compute_next(t_chunk_map *map, t_chunk_map *next, int *todo,
				int todo_count);
void		simulation_step(t_chunk_map *map);

// simulation_collect.c
void		sim_visit_neighbors(t_chunk_node *node, t_dedup_ctx *dedup,
				t_todo_ctx *todo);
int			count_neighbors(const t_chunk_map *m, int gx, int gy);
int			sim_collect_dedup(unsigned int *seen, unsigned int set_mask,
				int ncx, int ncy);
int			sim_collect_todo(t_chunk_map *map, int *todo, int cap);
t_dedup_ctx	sim_init_dedup(int cap);

#endif
