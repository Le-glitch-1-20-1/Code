/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_screens5.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:05:42 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/17 07:05:47 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"
#include "raylib.h"
#include "renderer.h"
#include "save.h"
#include "simulation.h"
#include <math.h>

void	draw_screen_load(t_app *app)
{
	char	out_path[256];
	bool	chosen;

	out_path[0] = 0;
	chosen = ui_draw_load_browser(out_path, sizeof(out_path));
	if (chosen)
	{
		map_init(&app->place_map);
		if (load_rle(out_path, &app->place_map, 0, 0) == 0)
		{
			center_map(&app->place_map);
			app->place_state = (t_place_state){0};
			app->place_loaded = true;
			app->screen = SCREEN_PLACE;
		}
		else
		{
			map_free(&app->place_map);
			app->running = false;
			app->screen = SCREEN_GAME;
		}
	}
	else if (IsKeyPressed(KEY_ESCAPE))
	{
		app->running = false;
		app->screen = SCREEN_GAME;
	}
}

void	draw_frame_menu(t_app *app)
{
	t_menu_action	mact;

	if (app->menu_just_opened)
	{
		app->menu_just_opened = false;
		return ;
	}
	mact = ui_draw_menu();
	if (mact == MENU_RESUME)
	{
		app->running = app->was_running;
		app->screen = SCREEN_GAME;
	}
	else if (mact == MENU_KEYBINDS)
		app->screen = SCREEN_KEYBINDS;
	else if (mact == MENU_CREDITS)
		app->screen = SCREEN_CREDITS;
	else if (mact == MENU_QUIT)
		CloseWindow();
}

void	draw_frame_screens(t_app *app)
{
	if (app->screen == SCREEN_GAME)
		draw_screen_game(app);
	else if (app->screen == SCREEN_RANDOM)
		draw_screen_random(app);
	else if (app->screen == SCREEN_SAVE_ZONE)
		draw_screen_save_zone(app);
	else if (app->screen == SCREEN_PLACE)
		draw_screen_place(app);
	else if (app->screen == SCREEN_MENU)
		draw_frame_menu(app);
	else if (app->screen == SCREEN_KEYBINDS)
	{
		if (ui_draw_keybinds(&app->keys) || IsKeyPressed(KEY_ESCAPE))
			app->screen = SCREEN_MENU;
	}
	else if (app->screen == SCREEN_CREDITS)
	{
		if (ui_draw_credits() || IsKeyPressed(KEY_ESCAPE))
			app->screen = SCREEN_MENU;
	}
	else if (app->screen == SCREEN_LOAD)
		draw_screen_load(app);
	else if (app->screen == SCREEN_SAVE)
		app->screen = SCREEN_SAVE_ZONE;
}

void	draw_frame(t_app *app)
{
	t_color_theme	th;

	th = get_theme(app->theme_idx);
	BeginDrawing();
	ClearBackground(th.bg);
	renderer_draw(&app->map, app->cam, app->show_grid,
		app->show_chunk_debug, app->theme_idx);
	draw_selections(app);
	draw_frame_screens(app);
	EndDrawing();
}

void	update(t_app *app, float dt)
{
	int		alive;
	int		idx;
	float	td;

	if (app->screen != SCREEN_GAME)
		return ;
	handle_game_input(app);
	if (!app->running)
		return ;
	app->tick_acc += dt;
	td = 1.0f / app->speed;
	while (app->tick_acc >= td)
	{
		simulation_step(&app->map);
		app->generation++;
		app->tick_acc -= td;
		alive = map_alive_count(&app->map);
		idx = app->pop_count % POP_HISTORY_LEN;
		app->pop_history[idx] = alive;
		app->pop_count++;
		if (alive > app->pop_max)
			app->pop_max = alive;
	}
}
