/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   simulation.h                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:08:33 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 09:46:22 by le-glitch        ###   ########.fr       */
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

int		count_neighbors(const t_chunk_map *m, int gx, int gy);
int		sim_collect_dedup(unsigned int *seen, unsigned int set_mask,
			int ncx, int ncy);
void	sim_visit_neighbors(t_chunk_node *node,
			t_dedup_ctx *dedup, t_todo_ctx *todo);
int		sim_collect_todo(t_chunk_map *map, int *todo, int cap);

void	simulation_step(t_chunk_map *map);

#endif
