/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   position.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: you <you@student.42.fr>                   +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 00:00:00 by you               #+#    #+#             */
/*   Updated: 2026/09/02 00:00:00 by you              ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "heart.h"

void	randomize_position(int square, int *pos_x, int *pos_y)
{
	int	width;
	int	height;

	srand(time(NULL));
	get_screen_resolution(&width, &height);
	*pos_x = get_random(0, width - square);
	*pos_y = get_random(0, height - square);
}
