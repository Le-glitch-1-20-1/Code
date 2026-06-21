/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_input-5.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:13:54 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:18:51 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"
#include "raylib.h"
#include "simulation.h"
#include <math.h>

void	handle_no_ctrl_keys(t_app *app);
void	handle_no_ctrl_misc(t_app *app);

void	handle_key_random(t_app *app)
{
	app->was_running = app->running;
	app->running = false;
	app->rand_state = (t_random_state){0};
	app->rand_state.density = 0.3f;
	app->screen = SCREEN_RANDOM;
}

void	handle_key_save(t_app *app)
{
	app->was_running = app->running;
	app->running = false;
	app->save_zone = (t_save_zone_state){0};
	snprintf(app->save_zone.name_buf,
		sizeof(app->save_zone.name_buf), "mon_pattern");
	app->screen = SCREEN_SAVE_ZONE;
}

static void	handle_no_ctrl_clear(t_app *app)
{
	t_key_config	*k;

	k = &app->keys;
	if (!IsKeyPressed(k->clear))
		return ;
	push_undo(app);
	map_free(&app->map);
	map_init(&app->map);
	app->generation = 0;
	app->drawing = false;
	app->running = false;
	app->pop_count = 0;
	app->pop_max = 0;
}

static void	handle_no_ctrl_center(t_app *app)
{
	t_key_config	*k;

	k = &app->keys;
	if (IsKeyPressed(k->center_view))
	{
		app->cam.offset.x = GetScreenWidth() / 2.0f;
		app->cam.offset.y = GetScreenHeight() / 2.0f;
	}
}

void	handle_no_ctrl(t_app *app)
{
	handle_no_ctrl_keys(app);
	handle_no_ctrl_clear(app);
	handle_no_ctrl_center(app);
	handle_no_ctrl_misc(app);
}
