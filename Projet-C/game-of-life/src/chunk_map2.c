/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/* chunk_map2.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/* By: student <student@student.42.fr>              +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/* Created: 2025/01/01 00:00:00 by student           #+#    #+#             */
/* Updated: 2025/01/01 00:00:00 by student          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "chunk_map.h"
#include <stdlib.h>
#include <string.h>

int	floor_div(int a, int b)
{
	return (a / b - (a % b != 0 && (a ^ b) < 0));
}

int	floor_mod(int a, int b)
{
	return (a - floor_div(a, b) * b);
}

void	map_remove(t_chunk_map *m, int cx, int cy)
{
	t_chunk_node	**pp;
	t_chunk_node	*node;
	unsigned int	idx;

	idx = (unsigned int)(cx * 1000003) ^ (unsigned int)(cy * 999983);
	idx = idx & MAP_MASK;
	pp = &m->buckets[idx];
	while (*pp)
	{
		node = *pp;
		if (node->chunk.cx == cx && node->chunk.cy == cy)
		{
			*pp = node->next;
			free(node);
			m->chunk_count--;
			return ;
		}
		pp = &node->next;
	}
}

void	map_remove_dead(t_chunk_map *m)
{
	t_chunk_node	**pp;
	t_chunk_node	*node;
	int				i;

	i = 0;
	while (i < MAP_SIZE)
	{
		pp = &m->buckets[i];
		while (*pp)
		{
			node = *pp;
			if (chunk_is_dead(&node->chunk))
			{
				*pp = node->next;
				free(node);
				m->chunk_count--;
			}
			else
				pp = &node->next;
		}
		i++;
	}
}

int	map_alive_count(const t_chunk_map *m)
{
	t_chunk_node	*node;
	int				total;
	int				i;

	total = 0;
	i = 0;
	while (i < MAP_SIZE)
	{
		node = m->buckets[i];
		while (node)
		{
			total += node->chunk.alive_count;
			node = node->next;
		}
		i++;
	}
	return (total);
}
