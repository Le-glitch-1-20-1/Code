/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_input-01.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:06:13 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 23:06:05 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	apply_zoom(t_app *app, float wheel)
{
	Vector2	m;
	float	f;
	float	z;
	float	ratio;

	if ((app->cam.zoom >= ZOOM_MAX && wheel > 0)
		|| (app->cam.zoom <= ZOOM_MIN && wheel < 0))
		return ;
	m = GetMousePosition();
	if (wheel > 0)
		f = 1.15f;
	else
		f = 1.0f / 1.15f;
	z = app->cam.zoom * f;
	if (z < ZOOM_MIN)
		z = ZOOM_MIN;
	if (z > ZOOM_MAX)
		z = ZOOM_MAX;
	if (z != app->cam.zoom)
	{
		ratio = z / app->cam.zoom;
		app->cam.offset.x = m.x + (app->cam.offset.x - m.x) * ratio;
		app->cam.offset.y = m.y + (app->cam.offset.y - m.y) * ratio;
		app->cam.zoom = z;
	}
}

void	handle_pan_keys(t_app *app)
{
	t_key_config	*k;

	k = &app->keys;
	if (IsKeyDown(k->pan_up))
		app->cam.offset.y += PAN_SPEED;
	if (IsKeyDown(k->pan_down))
		app->cam.offset.y -= PAN_SPEED;
	if (IsKeyDown(k->pan_left))
		app->cam.offset.x += PAN_SPEED;
	if (IsKeyDown(k->pan_right))
		app->cam.offset.x -= PAN_SPEED;
}

void	handle_pan_mouse(t_app *app, Vector2 mouse)
{
	if (IsMouseButtonPressed(MOUSE_BUTTON_MIDDLE))
	{
		app->mid_panning = true;
		app->mid_pan_origin = mouse;
		app->cam_origin = app->cam.offset;
	}
	if (app->mid_panning)
	{
		if (IsMouseButtonDown(MOUSE_BUTTON_MIDDLE))
		{
			app->cam.offset.x = app->cam_origin.x
				+ (mouse.x - app->mid_pan_origin.x);
			app->cam.offset.y = app->cam_origin.y
				+ (mouse.y - app->mid_pan_origin.y);
		}
		else
			app->mid_panning = false;
	}
}

void	handle_pan(t_app *app)
{
	Vector2	mouse;

	handle_pan_keys(app);
	mouse = GetMousePosition();
	handle_pan_mouse(app, mouse);
}
