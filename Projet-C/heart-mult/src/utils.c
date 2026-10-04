/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   utils.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: replace_me <replace_me@student.42.fr>     +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 00:00:00 by replace_me        #+#    #+#             */
/*   Updated: 2026/09/02 00:00:00 by replace_me       ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "heart.h"

int	get_random(int min, int max)
{
	return (min + rand() % (max - min + 1));
}

void	resolution(int *width, int *height)
{
	*width = GetMonitorWidth(GetCurrentMonitor());
	*height = GetMonitorHeight(GetCurrentMonitor());
}

void	randomizer(int square, int *pwidth, int *pheight)
{
	int	width;
	int	height;

	srand(time(NULL));
	resolution(&width, &height);
	*pwidth = get_random(0, width - square);
	*pheight = get_random(0, height - square);
}
