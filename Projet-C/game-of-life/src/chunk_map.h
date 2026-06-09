/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/* chunk_map.h                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/* By: student <student@student.42.fr>              +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/* Created: 2025/01/01 00:00:00 by student           #+#    #+#             */
/* Updated: 2025/01/01 00:00:00 by student          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef CHUNK_MAP_H
# define CHUNK_MAP_H

# include "chunk.h"

# define MAP_SIZE 4096
# define MAP_MASK 4095

/*
** Hashmap ouverte avec chainage par liste chainee.
** Chaque bucket pointe sur une liste de chunks alloues dynamiquement.
*/
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

void			map_init(t_chunk_map *m);
void			map_free(t_chunk_map *m);

t_chunk			*map_get(const t_chunk_map *m, int cx, int cy);
t_chunk			*map_get_or_create(t_chunk_map *m, int cx, int cy);

void			map_remove(t_chunk_map *m, int cx, int cy);
void			map_remove_dead(t_chunk_map *m);

int				map_alive_count(const t_chunk_map *m);

int				get_cell_global(const t_chunk_map *m, int x, int y);
void			set_cell_global(t_chunk_map *m, int x, int y, int v);

t_chunk_node		*map_first(const t_chunk_map *m, int *bucket_idx);
t_chunk_node		*map_next(const t_chunk_map *m, int *bucket_idx,
				t_chunk_node *current);

void			map_copy(t_chunk_map *dst, const t_chunk_map *src);

int	floor_div(int a, int b);
int	floor_mod(int a, int b);

#endif
