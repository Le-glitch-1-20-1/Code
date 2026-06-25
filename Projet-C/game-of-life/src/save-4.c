/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   save-2b.c                                          :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:09:04 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 11:22:12 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "save.h"

int	rle_parse_tag(t_rle_ctx *ctx, char tag, int count)
{
	int	i;

	if (tag == 'o')
	{
		i = 0;
		while (i < count)
		{
			set_cell_global(ctx->map, ctx->ox + *ctx->cur_x + i,
				ctx->oy + *ctx->cur_y, 1);
			i++;
		}
		*ctx->cur_x += count;
	}
	else if (tag == 'b')
		*ctx->cur_x += count;
	else if (tag == '$')
	{
		*ctx->cur_y += count;
		*ctx->cur_x = 0;
	}
	else if (tag == '!')
		return (1);
	return (0);
}

void	rle_parse_chars(t_rle_ctx *ctx, char *p, int *done)
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
			*done = rle_parse_tag(ctx, *p++, count);
	}
}

int	load_rle(const char *path, t_chunk_map *map, int offset_x, int offset_y)
{
	FILE		*f;
	char		line[1024];
	int			cur_x;
	int			cur_y;
	int			header_done;
	int			done;
	t_rle_ctx	ctx;

	f = fopen(path, "r");
	if (!f)
		return (-1);
	cur_x = 0;
	cur_y = 0;
	header_done = 0;
	done = 0;
	ctx = (t_rle_ctx){map, &cur_x, &cur_y, offset_x, offset_y};
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
		rle_parse_chars(&ctx, line, &done);
	}
	fclose(f);
	if (done)
		return (0);
	return (-1);
}
