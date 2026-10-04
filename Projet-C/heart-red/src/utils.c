/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   utils.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: you <you@student.42.fr>                   +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 00:00:00 by you               #+#    #+#             */
/*   Updated: 2026/09/02 00:00:00 by you              ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "heart.h"

int	get_random(int min, int max)
{
	return (min + rand() % (max - min + 1));
}

void	get_screen_resolution(int *width, int *height)
{
	*width = GetMonitorWidth(GetCurrentMonitor());
	*height = GetMonitorHeight(GetCurrentMonitor());
}
