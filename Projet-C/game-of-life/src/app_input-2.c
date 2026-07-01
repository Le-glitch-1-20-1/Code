/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_input-2.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:27:53 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 12:00:00 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	handle_drawing_start(t_app *app, int gx, int gy)
{
	bool	lb;
	bool	rb;

	lb = IsMouseButtonDown(MOUSE_BUTTON_LEFT);
	rb = IsMouseButtonDown(MOUSE_BUTTON_RIGHT);
	if (!(lb || rb) || app->drawing)
		return ;
	push_undo(app);
	app->drawing = true;
	if (lb)
		app->draw_val = 1;
	else
		app->draw_val = 0;
	app->last_gx = gx;
	app->last_gy = gy;
	set_cell_global(&app->map, gx, gy, app->draw_val);
}

void	handle_drawing_move(t_app *app, int gx, int gy)
{
	bool	lb;
	bool	rb;

	lb = IsMouseButtonDown(MOUSE_BUTTON_LEFT);
	rb = IsMouseButtonDown(MOUSE_BUTTON_RIGHT);
	if (!app->drawing || !(lb || rb))
		return ;
	draw_line_cells(&app->map,
		(t_rect){app->last_gx, app->last_gy, gx, gy}, app->draw_val);
	app->last_gx = gx;
	app->last_gy = gy;
}

void	handle_drawing(t_app *app, Vector2 mouse, bool on_ui)
{
	int	gx;
	int	gy;

	if (on_ui || app->clear_select_mode || app->copy_select_mode
		|| app->paste_mode || app->mid_panning)
		return ;
	gx = (int)floorf((mouse.x - app->cam.offset.x) / app->cam.zoom);
	gy = (int)floorf((mouse.y - app->cam.offset.y) / app->cam.zoom);
	handle_drawing_start(app, gx, gy);
	handle_drawing_move(app, gx, gy);
}

void	apply_random_fill(t_chunk_map *map, const t_random_state *rs)
{
	int	x;
	int	y;

	y = rs->y0;
	while (y <= rs->y1)
	{
		x = rs->x0;
		while (x <= rs->x1)
		{
			if ((float)rand() / (float)RAND_MAX < rs->density)
				set_cell_global(map, x, y, 1);
			x++;
		}
		y++;
	}
}
