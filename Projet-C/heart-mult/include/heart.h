/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   heart.h                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: replace_me <replace_me@student.42.fr>     +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 00:00:00 by replace_me        #+#    #+#             */
/*   Updated: 2026/09/02 00:00:00 by replace_me       ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef HEART_H
# define HEART_H

# include "raylib.h"
# include <stdio.h>
# include <stdlib.h>
# include <stdbool.h>
# include <time.h>
# include <math.h>

# define SQUARE_SIZE 150
# define RESOL 1000

typedef struct s_bounds
{
	float	minx;
	float	maxx;
	float	miny;
	float	maxy;
}	t_bounds;

typedef struct s_heart_params
{
	int		cx;
	int		cy;
	float	scale;
	float	thickness;
	float	time_offset;
}	t_heart_params;

int		get_random(int min, int max);
void	resolution(int *width, int *height);
void	randomizer(int square, int *pwidth, int *pheight);
void	heart_point(float t, float *x, float *y);
void	get_bounds(t_bounds *b);
void	build_points(Vector2 *points, t_heart_params *p,
			float offx, float offy);
void	draw_glow(Vector2 *points, float time_offset, float thickness);
void	draw_main_line(Vector2 *points, float time_offset, float thickness);
void	draw_heart_outline(t_heart_params *p);

#endif
