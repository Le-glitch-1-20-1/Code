/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   renderer_coords.c                                  :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:24:24 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 11:06:36 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "renderer.h"

Vector2	screen_to_cell(t_camera2d_gol cam, Vector2 screen)
{
	Vector2	result;

	result.x = (screen.x - cam.offset.x) / cam.zoom;
	result.y = (screen.y - cam.offset.y) / cam.zoom;
	return (result);
}

Vector2	cell_to_screen(t_camera2d_gol cam, float cx, float cy)
{
	Vector2	result;

	result.x = cx * cam.zoom + cam.offset.x;
	result.y = cy * cam.zoom + cam.offset.y;
	return (result);
}
