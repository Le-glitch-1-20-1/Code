/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   save-1.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:12:18 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 11:22:12 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "save.h"

void	bbox_update(const t_chunk *c, int lx, int ly, t_bbox *box)
{
	int	gx;
	int	gy;

	gx = c->cx * CHUNK_SIZE + lx;
	gy = c->cy * CHUNK_SIZE + ly;
	if (gx < box->x0)
		box->x0 = gx;
	if (gx > box->x1)
		box->x1 = gx;
	if (gy < box->y0)
		box->y0 = gy;
	if (gy > box->y1)
		box->y1 = gy;
}

void	bbox_scan_chunk(const t_chunk *c, t_bbox *box)
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
					bbox_update(c, lx, ly, box);
				lx++;
			}
		}
		ly++;
	}
}

void	map_bounding_box(const t_chunk_map *m, t_bbox *box)
{
	t_chunk	*node;
	int		bucket;

	box->x0 = 0x7FFFFFFF;
	box->y0 = 0x7FFFFFFF;
	box->x1 = -0x7FFFFFFF;
	box->y1 = -0x7FFFFFFF;
	node = map_first((t_chunk_map *)m, &bucket);
	while (node)
	{
		bbox_scan_chunk(node, box);
		node = map_next((t_chunk_map *)m, &bucket, node);
	}
	if (box->x0 == 0x7FFFFFFF)
		*box = (t_bbox){0, 0, 0, 0};
}

void	rle_write_token(FILE *f, t_rle_line *lb, int run, char cur)
{
	char	token[32];
	int		tlen;

	if (run == 1)
		tlen = snprintf(token, sizeof(token), "%c", cur);
	else
		tlen = snprintf(token, sizeof(token), "%d%c", run, cur);
	if (lb->len + tlen > 70)
	{
		lb->buf[(lb->len)++] = '\n';
		fwrite(lb->buf, 1, lb->len, f);
		lb->len = 0;
	}
	memcpy(lb->buf + lb->len, token, tlen);
	lb->len += tlen;
}

void	rle_write_row(FILE *f, const t_chunk_map *map, t_rle_line *lb,
			t_rle_row r)
{
	int		gx;
	int		run;
	char	cur;
	char	nxt;
	char	eol;

	gx = r.x0;
	while (gx <= r.last)
	{
		if (get_cell_global(map, gx, r.gy))
			cur = 'o';
		else
			cur = 'b';
		run = 1;
		while (gx + run <= r.last)
		{
			if (get_cell_global(map, gx + run, r.gy))
				nxt = 'o';
			else
				nxt = 'b';
			if (nxt != cur)
				break ;
			run++;
		}
		rle_write_token(f, lb, run, cur);
		gx += run;
	}
	if (r.gy < r.x1)
		eol = '$';
	else
		eol = '!';
	if (lb->len + 1 > 70)
	{
		lb->buf[(lb->len)++] = '\n';
		fwrite(lb->buf, 1, lb->len, f);
		lb->len = 0;
	}
	lb->buf[(lb->len)++] = eol;
}
