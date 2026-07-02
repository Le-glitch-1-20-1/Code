/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   save-5.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/27 21:05:20 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 21:05:20 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "save.h"

static int	rle_run_len(const t_chunk_map *map, int gx, t_rle_row r, char cur)
{
	int		run;
	char	nxt;

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
	return (run);
}

static void	rle_write_eol(FILE *f, t_rle_line *lb, t_rle_row r)
{
	char	eol;

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

void	rle_write_row(FILE *f, const t_chunk_map *map, t_rle_line *lb,
			t_rle_row r)
{
	int		gx;
	int		run;
	char	cur;

	gx = r.x0;
	while (gx <= r.last)
	{
		if (get_cell_global(map, gx, r.gy))
			cur = 'o';
		else
			cur = 'b';
		run = rle_run_len(map, gx, r, cur);
		rle_write_token(f, lb, run, cur);
		gx += run;
	}
	rle_write_eol(f, lb, r);
}
