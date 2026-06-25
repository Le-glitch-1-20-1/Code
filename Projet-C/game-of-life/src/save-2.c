/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   save-2.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:09:04 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/25 08:23:57 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "save.h"

int	rle_find_last(const t_chunk_map *map, int gy, int x0, int x1)
{
	int	gx;

	gx = x1;
	while (gx >= x0)
	{
		if (get_cell_global(map, gx, gy))
			return (gx);
		gx--;
	}
	return (x0 - 1);
}

void	save_rle_body(FILE *f, const t_chunk_map *map, t_bbox box)
{
	t_rle_line	lb;
	int			gy;
	int			last;

	lb.len = 0;
	gy = box.y0;
	while (gy <= box.y1)
	{
		last = rle_find_last(map, gy, box.x0, box.x1);
		rle_write_row(f, map, &lb, (t_rle_row){gy, box.x0, box.y1, last});
		gy++;
	}
	lb.buf[lb.len++] = '\n';
	fwrite(lb.buf, 1, lb.len, f);
}

int	save_rle(const char *path, const t_chunk_map *map)
{
	t_bbox	box;
	FILE	*f;

	map_bounding_box(map, &box);
	f = fopen(path, "w");
	if (!f)
		return (-1);
	if (box.x0 > box.x1)
	{
		fprintf(f, "x = 0, y = 0, rule = B3/S23\n!\n");
		fclose(f);
		return (0);
	}
	fprintf(f, "x = %d, y = %d, rule = B3/S23\n",
		box.x1 - box.x0 + 1, box.y1 - box.y0 + 1);
	save_rle_body(f, map, box);
	fclose(f);
	return (0);
}
