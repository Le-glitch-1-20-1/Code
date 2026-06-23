/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   save-2.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:09:04 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 22:13:59 by le-glitch        ###   ########.fr       */
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

int	save_rle(const char *path, const t_chunk_map *map)
{
	char	line_buf[512];
	int		line_len;
	int		x0;
	int		y0;
	int		x1;
	int		y1;
	int		gy;
	int		last;
	FILE	*f;

	map_bounding_box(map, &x0, &y0, &x1, &y1);
	f = fopen(path, "w");
	if (!f)
		return (-1);
	if (x0 > x1)
	{
		fprintf(f, "x = 0, y = 0, rule = B3/S23\n!\n");
		fclose(f);
		return (0);
	}
	fprintf(f, "x = %d, y = %d, rule = B3/S23\n",
		x1 - x0 + 1, y1 - y0 + 1);
	line_len = 0;
	gy = y0;
	while (gy <= y1)
	{
		last = rle_find_last(map, gy, x0, x1);
		rle_write_row(f, map, line_buf, &line_len, gy, x0, y1, last);
		gy++;
	}
	line_buf[line_len++] = '\n';
	fwrite(line_buf, 1, line_len, f);
	fclose(f);
	return (0);
}

int	rle_parse_tag(t_chunk_map *map, char tag, int count, int *cur_x,
		int *cur_y, int ox, int oy)
{
	int	i;

	if (tag == 'o')
	{
		i = 0;
		while (i < count)
		{
			set_cell_global(map, ox + *cur_x + i, oy + *cur_y, 1);
			i++;
		}
		*cur_x += count;
	}
	else if (tag == 'b')
		*cur_x += count;
	else if (tag == '$')
	{
		*cur_y += count;
		*cur_x = 0;
	}
	else if (tag == '!')
		return (1);
	return (0);
}

void	rle_parse_chars(t_chunk_map *map, char *p, int *done, int *cur_x,
			int *cur_y, int ox, int oy)
{
	int	count;

	while (*p && !*done)
	{
		if (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n')
		{
			p++;
			continue ;
		}
		count = 0;
		while (isdigit((unsigned char)*p))
			count = count * 10 + (*p++ - '0');
		if (count == 0)
			count = 1;
		if (*p)
			*done = rle_parse_tag(map, *p++, count, cur_x, cur_y, ox, oy);
	}
}

int	load_rle(const char *path, t_chunk_map *map, int offset_x, int offset_y)
{
	FILE	*f;
	char	line[1024];
	int		cur_x;
	int		cur_y;
	int		header_done;
	int		done;

	f = fopen(path, "r");
	if (!f)
		return (-1);
	cur_x = 0;
	cur_y = 0;
	header_done = 0;
	done = 0;
	while (!done && fgets(line, sizeof(line), f))
	{
		if (line[0] == '#')
			continue ;
		if (!header_done)
		{
			header_done = 1;
			if (line[0] == 'x' || line[0] == 'X')
				continue ;
		}
		rle_parse_chars(map, line, &done, &cur_x, &cur_y,
			offset_x, offset_y);
	}
	fclose(f);
	if (done)
		return (0);
	return (-1);
}
