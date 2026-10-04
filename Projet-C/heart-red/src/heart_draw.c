/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   heart_draw.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: you <you@student.42.fr>                   +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 00:00:00 by you               #+#    #+#             */
/*   Updated: 2026/09/02 00:00:00 by you              ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "heart.h"

void	draw_heart_glow(t_heart *heart)
{
	int		i;
	Color	glow;

	glow = Fade(heart->color, 0.25f);
	i = 0;
	while (i < heart->resol)
	{
		DrawLineEx(heart->points[i], heart->points[i + 1],
			heart->thickness + 4.0f, glow);
		i++;
	}
}

void	draw_heart_line(t_heart *heart)
{
	int	i;

	i = 0;
	while (i < heart->resol)
	{
		DrawLineEx(heart->points[i], heart->points[i + 1],
			heart->thickness, heart->color);
		DrawCircleV(heart->points[i], heart->thickness / 2.0f, heart->color);
		i++;
	}
}

void	draw_heart_outline(t_heart *heart)
{
	float	offx;
	float	offy;

	compute_heart_bounds(&offx, &offy);
	build_heart_points(heart, offx, offy);
	draw_heart_glow(heart);
	draw_heart_line(heart);
}
