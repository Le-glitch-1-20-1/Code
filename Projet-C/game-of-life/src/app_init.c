/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_init.c                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:29:40 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:18:31 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"
#include "chunk_map.h"
#include "config.h"
#include <stdlib.h>

static void	app_init_defaults(t_app *app)
{
	app->cam.offset = (Vector2){800, 450};
	app->cam.zoom = 12.0f;
	app->speed = 10.0f;
	app->show_grid = true;
	app->show_hud = true;
	app->screen = SCREEN_GAME;
	app->clipboard_valid = false;
	app->paste_mode = false;
	app->theme_idx = 0;
	app->pop_count = 0;
	app->pop_max = 0;
	app->undo_head = 0;
	app->undo_count = 0;
}

static void	app_init_undo(t_app *app)
{
	int	i;

	i = 0;
	while (i < UNDO_LEN)
	{
		app->undo_valid[i] = false;
		i++;
	}
}

t_app	*app_init(void)
{
	t_app	*app;

	app = (t_app *)calloc(1, sizeof(t_app));
	if (!app)
		return (NULL);
	app_init_defaults(app);
	app->keys = load_key_config(CONFIG_FILE);
	save_key_config(CONFIG_FILE, &app->keys);
	map_init(&app->map);
	map_init(&app->clipboard);
	app_init_undo(app);
	return (app);
}

void	app_cleanup(t_app *app)
{
	int	i;

	map_free(&app->map);
	map_free(&app->clipboard);
	if (app->place_loaded)
		map_free(&app->place_map);
	i = 0;
	while (i < UNDO_LEN)
	{
		if (app->undo_valid[i])
			map_free(&app->undo_stack[i]);
		i++;
	}
	free(app);
}
