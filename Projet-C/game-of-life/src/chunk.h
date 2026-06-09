/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   chunk.h                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/03 15:56:46 by le-glitch         #+#    #+#             */
/*   Updated: 2026/05/03 15:56:51 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef CHUNK_H
# define CHUNK_H

# include <stdint.h>

# define CHUNK_SIZE 16

/*
** Un chunk represente un bloc de 16x16 cellules.
** Chaque ligne est un uint16_t : 1 bit = 1 cellule.
** Memoire : 32 octets par chunk, tres cache-friendly.
*/
typedef struct s_chunk
{
	int			cx;
	int			cy;
	uint16_t	cells[CHUNK_SIZE];
	int			alive_count;
}	t_chunk;

static inline int	chunk_get(const t_chunk *c, int x, int y)
{
	return ((c->cells[y] >> x) & 1);
}

static inline void	chunk_set(t_chunk *c, int x, int y, int v)
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

static inline void	chunk_clear(t_chunk *c)
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

static inline int	chunk_is_dead(const t_chunk *c)
{
	return (c->alive_count == 0);
}

#endif
