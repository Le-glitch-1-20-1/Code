/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_screens-6.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:08:21 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/25 08:20:21 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	draw_screen_place_rotate(t_app *app)
{
	t_chunk_map	rotated;

	rotate_map_90(&app->place_map, &rotated);
	map_free(&app->place_map);
	app->place_map = rotated;
	center_map(&app->place_map);
	app->place_state.rotation = (app->place_state.rotation + 1) % 4;
}

void	draw_place_info(t_app *app, int gx, int gy)
{
	t_bbox	box;

	map_bounding_box(&app->place_map, &box);
	draw_selection_info_box((t_sel_box){"Pattern", gx + box.x0, gy + box.y0,
		gx + box.x1, gy + box.y1, map_alive_count(&app->place_map)});
}

void	handle_place_drop(t_app *app, Vector2 mpos, int gx, int gy)
{
	if (!app->mid_panning && mpos.y <= GetScreenHeight() - 100
		&& IsMouseButtonReleased(MOUSE_BUTTON_LEFT))
	{
		push_undo(app);
		stamp_pattern(app, gx, gy);
		map_free(&app->place_map);
		app->place_loaded = false;
		app->screen = SCREEN_GAME;
	}
	if (IsKeyPressed(KEY_ESCAPE))
	{
		map_free(&app->place_map);
		app->place_loaded = false;
		app->screen = SCREEN_GAME;
	}
}

void	draw_screen_place(t_app *app)
{
	Vector2	mpos;
	int		gx;
	int		gy;
	float	wheel;

	draw_place_preview(app);
	handle_pan(app);
	if (IsKeyPressed(app->keys.toggle_grid))
		app->show_grid = !app->show_grid;
	ui_draw_toolbar(app->running, &app->speed, app->theme_idx);
	mpos = GetMousePosition();
	gx = (int)floorf((mpos.x - app->cam.offset.x) / app->cam.zoom);
	gy = (int)floorf((mpos.y - app->cam.offset.y) / app->cam.zoom);
	draw_place_info(app, gx, gy);
	wheel = GetMouseWheelMove();
	if (wheel != 0)
		apply_zoom(app, wheel);
	if (IsKeyPressed(app->keys.rotate))
		draw_screen_place_rotate(app);
	handle_place_drop(app, mpos, gx, gy);
}
