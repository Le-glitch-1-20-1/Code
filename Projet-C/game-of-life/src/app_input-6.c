/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_input6.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:37:06 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/17 07:37:07 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"
#include "raylib.h"
#include "simulation.h"
#include <math.h>

int	handle_escape(t_app *app, bool ctrl);
void	handle_ctrl_shortcuts(t_app *app);

void	handle_speed(t_app *app)
{
	t_key_config	*k;

	k = &app->keys;
	if (IsKeyDown(k->speed_up))
	{
		app->speed += 0.5f;
		if (app->speed > 120)
			app->speed = 120;
	}
	if (IsKeyDown(k->speed_down))
	{
		app->speed -= 0.5f;
		if (app->speed < 1)
			app->speed = 1;
	}
}

void	handle_game_input(t_app *app)
{
	t_key_config	*k;
	Vector2			mouse;
	bool			ctrl;
	bool			on_ui;
	float			wheel;

	k = &app->keys;
	wheel = GetMouseWheelMove();
	if (wheel != 0.0f)
		apply_zoom(app, wheel);
	handle_pan(app);
	mouse = GetMousePosition();
	on_ui = (mouse.y <= 42) || (mouse.y > GetScreenHeight() - 28);
	handle_drawing(app, mouse, on_ui);
	if (!IsMouseButtonDown(MOUSE_BUTTON_LEFT)
		&& !IsMouseButtonDown(MOUSE_BUTTON_RIGHT))
		app->drawing = false;
	ctrl = IsKeyDown(k->mod_save);
	if (handle_escape(app, ctrl))
		return ;
	if (!ctrl)
		handle_no_ctrl(app);
	handle_speed(app);
	if (ctrl)
		handle_ctrl_shortcuts(app);
	handle_clear_select(app, mouse, on_ui);
	handle_copy_select(app, mouse, on_ui);
}
