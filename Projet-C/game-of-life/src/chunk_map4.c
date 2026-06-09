/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/* chunk_map4.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/* By: student <student@student.42.fr>              +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/* Created: 2025/01/01 00:00:00 by student           #+#    #+#             */
/* Updated: 2025/01/01 00:00:00 by student          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "chunk_map.h"
#include <stdlib.h>

int	get_cell_global(const t_chunk_map *m, int x, int y)
{
	t_chunk	*c;
	int		cx;
	int		cy;

	cx = floor_div(x, CHUNK_SIZE);
	cy = floor_div(y, CHUNK_SIZE);
	c = map_get(m, cx, cy);
	if (!c)
		return (0);
	return (chunk_get(c, floor_mod(x, CHUNK_SIZE), floor_mod(y, CHUNK_SIZE)));
}

void	set_cell_global(t_chunk_map *m, int x, int y, int v)
{
	t_chunk	*c;
	int		cx;
	int		cy;

	cx = floor_div(x, CHUNK_SIZE);
	cy = floor_div(y, CHUNK_SIZE);
	if (v)
	{
		c = map_get_or_create(m, cx, cy);
		if (c)
			chunk_set(c, floor_mod(x, CHUNK_SIZE), floor_mod(y, CHUNK_SIZE), 1);
	}
	else
	{
		c = map_get(m, cx, cy);
		if (c)
			chunk_set(c, floor_mod(x, CHUNK_SIZE), floor_mod(y, CHUNK_SIZE), 0);
	}
}
