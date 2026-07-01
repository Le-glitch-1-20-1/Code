/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_screens-4.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:08:21 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 12:00:00 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	handle_random_result(t_app *app)
{
	if (app->rand_state.confirmed)
	{
		push_undo(app);
		apply_random_fill(&app->map, &app->rand_state);
		app->rand_state = (t_random_state){0};
		app->running = false;
		app->screen = SCREEN_GAME;
	}
	if (app->rand_state.cancelled || IsKeyPressed(KEY_ESCAPE))
	{
		app->rand_state = (t_random_state){0};
		app->running = false;
		app->screen = SCREEN_GAME;
	}
}

void	draw_screen_random(t_app *app)
{
	float	wheel;

	handle_pan(app);
	wheel = GetMouseWheelMove();
	if (wheel != 0)
		apply_zoom(app, wheel);
	if (IsKeyPressed(app->keys.toggle_grid))
		app->show_grid = !app->show_grid;
	ui_draw_toolbar(app->running, &app->speed, app->theme_idx);
	if (app->rand_state.phase == 0)
	{
		if (app->rand_state.dragging)
			draw_screen_random_sel(app);
		else
			draw_selection_info_box((t_sel_box){"Hasard", 0, 0, -1, -1, 0});
	}
	ui_draw_random_overlay(&app->rand_state, app->cam);
	handle_random_result(app);
}

void	draw_screen_save_zone_rect(t_app *app)
{
	float	sx;
	float	sy;
	float	rw;
	float	rh;

	sx = app->save_zone.x0 * app->cam.zoom + app->cam.offset.x;
	sy = app->save_zone.y0 * app->cam.zoom + app->cam.offset.y;
	rw = (app->save_zone.x1 - app->save_zone.x0 + 1) * app->cam.zoom;
	rh = (app->save_zone.y1 - app->save_zone.y0 + 1) * app->cam.zoom;
	DrawRectangle((int)sx, (int)sy, (int)rw, (int)rh,
		(Color){221, 185, 60, 25});
	DrawRectangleLinesEx((Rectangle){sx, sy, rw, rh}, 2.0f,
		(Color){221, 185, 60, 200});
}

void	handle_save_zone_ready(t_app *app, const char *out_path)
{
	t_rect	r;

	if (system("mkdir -p assets/patterns") != 0)
	{
	}
	r = (t_rect){app->save_zone.x0, app->save_zone.y0,
		app->save_zone.x1, app->save_zone.y1};
	save_zone_rle(out_path, &app->map, r);
	app->running = false;
	app->screen = SCREEN_GAME;
}

void	draw_screen_save_zone(t_app *app)
{
	char	out_path[256];
	bool	ready;

	handle_pan(app);
	if (IsKeyPressed(app->keys.toggle_grid))
		app->show_grid = !app->show_grid;
	ui_draw_toolbar(app->running, &app->speed, app->theme_idx);
	if (app->save_zone.phase == 1)
		draw_screen_save_zone_rect(app);
	out_path[0] = 0;
	ready = ui_draw_save_zone(&app->save_zone, app->cam,
			out_path, sizeof(out_path));
	if (ready)
		handle_save_zone_ready(app, out_path);
	else if (app->save_zone.cancelled)
	{
		app->running = false;
		app->screen = SCREEN_GAME;
	}
}
