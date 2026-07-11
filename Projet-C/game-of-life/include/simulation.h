/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   simulation.h                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:08:33 by le-glitch         #+#    #+#             */
/*   Updated: 2026/07/11 08:31:26 by le-glitch        ###   ########.fr       */
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

typedef struct s_chunk_nbrs
{
	const t_chunk	*c[3][3];
}	t_chunk_nbrs;

typedef struct s_cell_pos
{
	int	cx;
	int	cy;
	int	lx;
	int	ly;
}	t_cell_pos;

// simulation-1.c
void		sim_fetch_nbrs(const t_chunk_map *map, int cx, int cy,
				t_chunk_nbrs *nb);
void		sim_step_chunk(t_chunk_map *map, t_chunk_map *next, int *todo,
				int i);
void		sim_compute_next(t_chunk_map *map, t_chunk_map *next, int *todo,
				int todo_count);
void		simulation_step(t_chunk_map *map);
t_chunk		*sim_write_cell(t_chunk_map *next, t_chunk *out, t_cell_pos p);

// simulation-2.c
void		sim_visit_neighbors(t_chunk *node, t_dedup_ctx *dedup,
				t_todo_ctx *todo);
int			sim_collect_dedup(unsigned int *seen, unsigned int set_mask,
				int ncx, int ncy);
int			sim_collect_todo(t_chunk_map *map, int *todo, int cap);
t_dedup_ctx	sim_init_dedup(int cap);

// simulation-3.c
void		sim_wrap_axis(int *lc, int *bc);
int			sim_local_get(t_chunk_nbrs *nb, int lx, int ly);
int			sim_local_neighbors(t_chunk_nbrs *nb, int lx, int ly);
int			sim_cell_will_live(t_chunk_nbrs *nb, int lx, int ly);

#endif
