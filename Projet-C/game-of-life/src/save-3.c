/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   save-3.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:27:10 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/25 08:24:39 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "save.h"

void	json_write_chunk_row(FILE *f, const t_chunk *c, int ly, int *first)
{
	int	lx;

	lx = 0;
	while (lx < CHUNK_SIZE)
	{
		if (chunk_get(c, lx, ly))
		{
			if (!*first)
				fputc(',', f);
			fprintf(f, "[%d,%d]",
				c->cx * CHUNK_SIZE + lx, c->cy * CHUNK_SIZE + ly);
			*first = 0;
		}
		lx++;
	}
}

void	json_write_cells(FILE *f, const t_chunk_map *map)
{
	t_chunk	*node;
	int		bucket;
	int		first;
	int		ly;

	first = 1;
	node = map_first((t_chunk_map *)map, &bucket);
	while (node)
	{
		ly = 0;
		while (ly < CHUNK_SIZE)
		{
			if (node->cells[ly])
				json_write_chunk_row(f, node, ly, &first);
			ly++;
		}
		node = map_next((t_chunk_map *)map, &bucket, node);
	}
}

int	save_json(const char *path, const char *name, const t_chunk_map *map)
{
	FILE	*f;

	f = fopen(path, "w");
	if (!f)
		return (-1);
	fprintf(f, "{\"name\":\"%s\",\"cells\":[", name);
	json_write_cells(f, map);
	fprintf(f, "]}\n");
	fclose(f);
	return (0);
}

int	load_json(const char *path, t_chunk_map *map, int offset_x, int offset_y)
{
	FILE	*f;
	int		c;
	int		x;
	int		y;

	f = fopen(path, "r");
	if (!f)
		return (-1);
	c = fgetc(f);
	while (c != EOF)
	{
		if (c == '[' && fscanf(f, "%d,%d]", &x, &y) == 2)
			set_cell_global(map, offset_x + x, offset_y + y, 1);
		c = fgetc(f);
	}
	fclose(f);
	return (0);
}
