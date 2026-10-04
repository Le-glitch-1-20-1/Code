/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   heart_build.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: you <you@student.42.fr>                   +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 00:00:00 by you               #+#    #+#             */
/*   Updated: 2026/09/02 00:00:00 by you              ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "heart.h"

void	build_heart_points(t_heart *heart, float offx, float offy)
{
	float	t;
	float	x;
	float	y;
	int		i;

	i = 0;
	while (i <= heart->resol)
	{
		t = (2 * PI * i) / heart->resol;
		heart_point(t, &x, &y);
		heart->points[i].x = heart->cx + heart->scale * (x - offx);
		heart->points[i].y = heart->cy + heart->scale * (y - offy);
		i++;
	}
}
