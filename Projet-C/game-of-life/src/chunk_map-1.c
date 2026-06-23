/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   chunk_map-1.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:10:42 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 15:53:15 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "chunk.h"

unsigned int	hash_coord(int cx, int cy)
{
	unsigned int	h;

	h = (unsigned int)(cx * 1000003) ^ (unsigned int)(cy * 999983);
	return (h & MAP_MASK);
}

void	map_init(t_chunk_map *m)
{
	memset(m->buckets, 0, sizeof(m->buckets));
	m->chunk_count = 0;
}

void	map_free(t_chunk_map *m)
{
	t_chunk_node	*node;
	t_chunk_node	*next;
	int				i;

	i = 0;
	while (i < MAP_SIZE)
	{
		node = m->buckets[i];
		while (node)
		{
			next = node->next;
			free(node);
			node = next;
		}
		m->buckets[i] = NULL;
		i++;
	}
	m->chunk_count = 0;
}

t_chunk	*map_get(const t_chunk_map *m, int cx, int cy)
{
	t_chunk_node	*node;
	unsigned int	idx;

	idx = hash_coord(cx, cy);
	node = m->buckets[idx];
	while (node)
	{
		if (node->chunk.cx == cx && node->chunk.cy == cy)
			return (&node->chunk);
		node = node->next;
	}
	return (NULL);
}

t_chunk	*map_get_or_create(t_chunk_map *m, int cx, int cy)
{
	t_chunk_node	*node;
	t_chunk_node	*new_node;
	unsigned int	idx;

	idx = hash_coord(cx, cy);
	node = m->buckets[idx];
	while (node)
	{
		if (node->chunk.cx == cx && node->chunk.cy == cy)
			return (&node->chunk);
		node = node->next;
	}
	new_node = (t_chunk_node *)calloc(1, sizeof(t_chunk_node));
	if (!new_node)
		return (NULL);
	new_node->chunk.cx = cx;
	new_node->chunk.cy = cy;
	new_node->next = m->buckets[idx];
	m->buckets[idx] = new_node;
	m->chunk_count++;
	return (&new_node->chunk);
}
