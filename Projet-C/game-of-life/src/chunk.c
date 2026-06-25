/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   chunk.c                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:13:14 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 11:01:05 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "chunk.h"

int	chunk_get(const t_chunk *c, int x, int y)
{
	return ((c->cells[y] >> x) & 1);
}

void	chunk_set(t_chunk *c, int x, int y, int v)
{
	if (v)
	{
		if (!chunk_get(c, x, y))
		{
			c->cells[y] |= (1u << x);
			c->alive_count++;
		}
	}
	else
	{
		if (chunk_get(c, x, y))
		{
			c->cells[y] &= ~(1u << x);
			c->alive_count--;
		}
	}
}

void	chunk_clear(t_chunk *c)
{
	int	i;

	i = 0;
	while (i < CHUNK_SIZE)
	{
		c->cells[i] = 0;
		i++;
	}
	c->alive_count = 0;
}

int	chunk_is_dead(const t_chunk *c)
{
	return (c->alive_count == 0);
}
