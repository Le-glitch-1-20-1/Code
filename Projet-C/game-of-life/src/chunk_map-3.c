/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   chunk_map-3.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:16:21 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 09:10:41 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "chunk.h"

t_chunk_node	*map_first(const t_chunk_map *m, int *bucket_idx)
{
	int	i;

	i = 0;
	while (i < MAP_SIZE)
	{
		if (m->buckets[i])
		{
			*bucket_idx = i;
			return (m->buckets[i]);
		}
		i++;
	}
	*bucket_idx = MAP_SIZE;
	return (NULL);
}

t_chunk_node	*map_next(const t_chunk_map *m, int *bucket_idx,
	t_chunk_node *current)
{
	int	i;

	if (current->next)
		return (current->next);
	i = *bucket_idx + 1;
	while (i < MAP_SIZE)
	{
		if (m->buckets[i])
		{
			*bucket_idx = i;
			return (m->buckets[i]);
		}
		i++;
	}
	*bucket_idx = MAP_SIZE;
	return (NULL);
}

void	map_copy(t_chunk_map *dst, const t_chunk_map *src)
{
	t_chunk_node	*node;
	t_chunk			*dc;
	int				bucket;

	node = map_first(src, &bucket);
	while (node)
	{
		dc = map_get_or_create(dst, node->chunk.cx, node->chunk.cy);
		if (dc)
			*dc = node->chunk;
		node = map_next(src, &bucket, node);
	}
}
