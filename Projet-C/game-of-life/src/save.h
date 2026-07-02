/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   save.h                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:02:19 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/25 09:05:36 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef SAVE_H
# define SAVE_H

# include "main.h"
# include "chunk.h"

typedef struct s_bbox
{
	int	x0;
	int	y0;
	int	x1;
	int	y1;
}	t_bbox;

typedef struct s_rle_line
{
	char	buf[512];
	int		len;
}	t_rle_line;

typedef struct s_rle_row
{
	int	gy;
	int	x0;
	int	x1;
	int	last;
}	t_rle_row;

typedef struct s_rle_ctx
{
	t_chunk_map	*map;
	int			*cur_x;
	int			*cur_y;
	int			ox;
	int			oy;
}	t_rle_ctx;

// save-1.c
void		bbox_update(const t_chunk *c, int lx, int ly, t_bbox *box);
void		bbox_scan_chunk(const t_chunk *c, t_bbox *box);
void		map_bounding_box(const t_chunk_map *m, t_bbox *box);
void		rle_write_token(FILE *f, t_rle_line *lb, int run, char cur);

// save-5.c
void		rle_write_row(FILE *f, const t_chunk_map *map, t_rle_line *lb,
				t_rle_row r);

// save-2.c
void		save_rle_body(FILE *f, const t_chunk_map *map, t_bbox box);
int			rle_find_last(const t_chunk_map *map, int gy, int x0, int x1);
int			save_rle(const char *path, const t_chunk_map *map);

// save-3.c
void		json_write_cells(FILE *f, const t_chunk_map *map);
void		json_write_chunk_row(FILE *f, const t_chunk *c, int ly,
				int *first);
int			save_json(const char *path, const char *name,
				const t_chunk_map *map);
int			load_json(const char *path, t_chunk_map *map, int offset_x,
				int offset_y);

// save-4.c
void		rle_parse_chars(t_rle_ctx *ctx, char *p, int *done);
int			rle_parse_tag(t_rle_ctx *ctx, char tag, int count);
int			rle_read_file(FILE *f, t_rle_ctx *ctx);
int			load_rle(const char *path, t_chunk_map *map, int offset_x,
				int offset_y);

#endif
