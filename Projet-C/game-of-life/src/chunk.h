/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   chunk.h                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:13:14 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 09:45:39 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef CHUNK_H
# define CHUNK_H

# include "main.h"

# define CHUNK_SIZE 16
# define MAP_SIZE 4096
# define MAP_MASK 4095

typedef struct s_chunk
{
	int			cx;
	int			cy;
	uint16_t	cells[CHUNK_SIZE];
	int			alive_count;
}	t_chunk;

typedef struct s_chunk_node
{
	t_chunk				chunk;
	struct s_chunk_node	*next;
}	t_chunk_node;

typedef struct s_chunk_map
{
	t_chunk_node	*buckets[MAP_SIZE];
	int				chunk_count;
}	t_chunk_map;

t_chunk			*map_get(const t_chunk_map *m, int cx, int cy);
t_chunk			*map_get_or_create(t_chunk_map *m, int cx, int cy);
t_chunk_node	*map_first(const t_chunk_map *m, int *bucket_idx);
t_chunk_node	*map_next(const t_chunk_map *m, int *bucket_idx,
					t_chunk_node *current);

void			map_remove(t_chunk_map *m, int cx, int cy);
void			map_remove_dead(t_chunk_map *m);
void			map_init(t_chunk_map *m);
void			map_free(t_chunk_map *m);
void			map_copy(t_chunk_map *dst, const t_chunk_map *src);
void			set_cell_global(t_chunk_map *m, int x, int y, int v);
void			chunk_set(t_chunk *c, int x, int y, int v);
void			chunk_clear(t_chunk *c);
int				map_alive_count(const t_chunk_map *m);
int				get_cell_global(const t_chunk_map *m, int x, int y);
int				floor_div(int a, int b);
int				chunk_get(const t_chunk *c, int x, int y);
int				chunk_is_dead(const t_chunk *c);
int				floor_mod(int a, int b);

#endif
