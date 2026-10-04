/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   heart.h                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: you <you@student.42.fr>                   +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 00:00:00 by you               #+#    #+#             */
/*   Updated: 2026/09/02 00:00:00 by you              ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef HEART_H
# define HEART_H

# include "raylib.h"
# include <stdio.h>
# include <stdlib.h>
# include <time.h>
# include <math.h>

# define WINDOW_SIZE 150
# define HEART_RESOLUTION 1000

typedef struct s_heart
{
	Vector2	*points;
	int		resol;
	int		cx;
	int		cy;
	float	scale;
	float	thickness;
	Color	color;
}	t_heart;

typedef struct s_bounds
{
	float	minx;
	float	maxx;
	float	miny;
	float	maxy;
}	t_bounds;

int		get_random(int min, int max);
void	get_screen_resolution(int *width, int *height);
void	randomize_position(int square, int *pos_x, int *pos_y);
void	heart_point(float t, float *x, float *y);
void	compute_heart_bounds(float *offx, float *offy);
void	build_heart_points(t_heart *heart, float offx, float offy);
void	draw_heart_glow(t_heart *heart);
void	draw_heart_line(t_heart *heart);
void	draw_heart_outline(t_heart *heart);

#endif
