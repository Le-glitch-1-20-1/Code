/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   save.h                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:37:31 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/17 07:37:32 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef SAVE_H
# define SAVE_H

# include "chunk_map.h"
# include <stdio.h>
# include <stdlib.h>
# include <string.h>
# include <ctype.h>

void		bbox_update(const t_chunk *c, int lx, int ly,
		int *x0, int *y0, int *x1, int *y1);
void		bbox_scan_chunk(const t_chunk *c,
		int *x0, int *y0, int *x1, int *y1);
void		map_bounding_box(const t_chunk_map *m,
		int *x0, int *y0, int *x1, int *y1);
void		rle_write_token(FILE *f, char *line_buf,
		int *line_len, int run, char cur);
void		rle_write_row(FILE *f, const t_chunk_map *map,
		char *line_buf, int *line_len, int gy, int x0, int x1, int last);
int		rle_find_last(const t_chunk_map *map, int gy, int x0, int x1);
int		save_rle(const char *path, const t_chunk_map *map);
int		rle_parse_tag(t_chunk_map *map, char tag,
		int count, int *cur_x, int *cur_y, int ox, int oy);
void		rle_parse_chars(t_chunk_map *map, char *p,
		int *done, int *cur_x, int *cur_y, int ox, int oy);
int		load_rle(const char *path, t_chunk_map *map,
		int offset_x, int offset_y);
void		json_write_cells(FILE *f, const t_chunk_map *map);
int		save_json(const char *path, const char *name,
		const t_chunk_map *map);
int		load_json(const char *path, t_chunk_map *map,
		int offset_x, int offset_y);

#endif
