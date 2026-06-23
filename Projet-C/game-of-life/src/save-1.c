/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   save-1.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:12:18 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 09:12:59 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "save.h"

void	bbox_update(const t_chunk *c, int lx, int ly,
	int *x0, int *y0, int *x1, int *y1)
{
	int	gx;
	int	gy;

	gx = c->cx * CHUNK_SIZE + lx;
	gy = c->cy * CHUNK_SIZE + ly;
	if (gx < *x0)
		*x0 = gx;
	if (gx > *x1)
		*x1 = gx;
	if (gy < *y0)
		*y0 = gy;
	if (gy > *y1)
		*y1 = gy;
}

void	bbox_scan_chunk(const t_chunk *c,
	int *x0, int *y0, int *x1, int *y1)
{
	int	lx;
	int	ly;

	ly = 0;
	while (ly < CHUNK_SIZE)
	{
		if (c->cells[ly])
		{
			lx = 0;
			while (lx < CHUNK_SIZE)
			{
				if (chunk_get(c, lx, ly))
					bbox_update(c, lx, ly, x0, y0, x1, y1);
				lx++;
			}
		}
		ly++;
	}
}

void	map_bounding_box(const t_chunk_map *m,
	int *x0, int *y0, int *x1, int *y1)
{
	t_chunk_node	*node;
	int				bucket;

	*x0 = 0x7FFFFFFF;
	*y0 = 0x7FFFFFFF;
	*x1 = -0x7FFFFFFF;
	*y1 = -0x7FFFFFFF;
	node = map_first((t_chunk_map *)m, &bucket);
	while (node)
	{
		bbox_scan_chunk(&node->chunk, x0, y0, x1, y1);
		node = map_next((t_chunk_map *)m, &bucket, node);
	}
	if (*x0 == 0x7FFFFFFF)
	{
		*x0 = 0;
		*y0 = 0;
		*x1 = 0;
		*y1 = 0;
	}
}

void	rle_write_token(FILE *f, char *line_buf,
	int *line_len, int run, char cur)
{
	char	token[32];
	int		tlen;

	if (run == 1)
		tlen = snprintf(token, sizeof(token), "%c", cur);
	else
		tlen = snprintf(token, sizeof(token), "%d%c", run, cur);
	if (*line_len + tlen > 70)
	{
		line_buf[(*line_len)++] = '\n';
		fwrite(line_buf, 1, *line_len, f);
		*line_len = 0;
	}
	memcpy(line_buf + *line_len, token, tlen);
	*line_len += tlen;
}

void	rle_write_row(FILE *f, const t_chunk_map *map,
	char *line_buf, int *line_len, int gy, int x0, int x1, int last)
{
	int		gx;
	int		run;
	char	cur;
	char	nxt;
	char	eol;

	gx = x0;
	while (gx <= last)
	{
		if (get_cell_global(map, gx, gy))
			cur = 'o';
		else
			cur = 'b';
		run = 1;
		while (gx + run <= last)
		{
			if (get_cell_global(map, gx + run, gy))
				nxt = 'o';
			else
				nxt = 'b';
			if (nxt != cur)
				break ;
			run++;
		}
		rle_write_token(f, line_buf, line_len, run, cur);
		gx += run;
	}
	if (gy < x1)
		eol = '$';
	else
		eol = '!';
	if (*line_len + 1 > 70)
	{
		line_buf[(*line_len)++] = '\n';
		fwrite(line_buf, 1, *line_len, f);
		*line_len = 0;
	}
	line_buf[(*line_len)++] = eol;
}
