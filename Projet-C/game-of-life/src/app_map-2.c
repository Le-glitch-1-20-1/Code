/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_map-2.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:23:22 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 07:26:14 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"
#include "chunk_map.h"
#include "save.h"

#include "main.h"

int	save_zone_rle(const char *path, const t_chunk_map *src,
	int x0, int y0, int x1, int y1)
{
	t_chunk_map	tmp;
	int			r;
	int			x;
	int			y;

	map_init(&tmp);
	y = y0;
	while (y <= y1)
	{
		x = x0;
		while (x <= x1)
		{
			if (get_cell_global(src, x, y))
				set_cell_global(&tmp, x - x0, y - y0, 1);
			x++;
		}
		y++;
	}
	r = save_rle(path, &tmp);
	map_free(&tmp);
	return (r);
}
