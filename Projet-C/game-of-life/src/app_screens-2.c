/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_screens-2.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:17:07 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 11:28:58 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	fill_pop_buf(t_app *app, int *pbuf, int *pn)
{
	int	ph;
	int	pstart;
	int	i;

	ph = app->pop_count;
	if (ph > POP_HISTORY_LEN)
		pstart = ph - POP_HISTORY_LEN;
	else
		pstart = 0;
	*pn = ph - pstart;
	if (*pn > POP_HISTORY_LEN)
		*pn = POP_HISTORY_LEN;
	i = 0;
	while (i < *pn)
	{
		pbuf[i] = app->pop_history[(pstart + i) % POP_HISTORY_LEN];
		i++;
	}
}

void	draw_screen_game_hud(t_app *app)
{
	Vector2	mpos;
	int		pbuf[POP_HISTORY_LEN];
	int		pn;
	int		gx;
	int		gy;

	mpos = GetMousePosition();
	gx = (int)floorf((mpos.x - app->cam.offset.x) / app->cam.zoom);
	gy = (int)floorf((mpos.y - app->cam.offset.y) / app->cam.zoom);
	fill_pop_buf(app, pbuf, &pn);
	ui_draw_hud(app->generation, app->running, app->speed,
		map_alive_count(&app->map), gx, gy, pbuf, pn, app->pop_max);
}

void	draw_screen_game(t_app *app)
{
	t_ui_action	act;

	act = ui_draw_toolbar(app->running, &app->speed, app->theme_idx);
	handle_toolbar_action(app, act);
	if (!app->show_hud)
		return ;
	draw_screen_game_hud(app);
}

void	get_rand_bounds(t_app *app, t_rect *out)
{
	if (app->rand_state.x0 < app->rand_state.x1)
		out->xa = app->rand_state.x0;
	else
		out->xa = app->rand_state.x1;
	if (app->rand_state.x0 > app->rand_state.x1)
		out->xb = app->rand_state.x0;
	else
		out->xb = app->rand_state.x1;
	if (app->rand_state.y0 < app->rand_state.y1)
		out->ya = app->rand_state.y0;
	else
		out->ya = app->rand_state.y1;
	if (app->rand_state.y0 > app->rand_state.y1)
		out->yb = app->rand_state.y0;
	else
		out->yb = app->rand_state.y1;
}

void	draw_screen_random_sel(t_app *app)
{
	t_rect	r;
	float	sx;
	float	sy;
	float	rw;
	float	rh;
	int		alive;

	get_rand_bounds(app, &r);
	sx = r.xa * app->cam.zoom + app->cam.offset.x;
	sy = r.ya * app->cam.zoom + app->cam.offset.y;
	rw = (r.xb - r.xa + 1) * app->cam.zoom;
	rh = (r.yb - r.ya + 1) * app->cam.zoom;
	DrawRectangle((int)sx, (int)sy, (int)rw, (int)rh,
		(Color){221, 185, 60, 40});
	DrawRectangleLinesEx((Rectangle){sx, sy, rw, rh}, 2.0f,
		(Color){221, 185, 60, 200});
	alive = (int)((r.xb - r.xa + 1) * (r.yb - r.ya + 1)
			* app->rand_state.density);
	draw_selection_info_box((t_sel_box){"Hasard", r.xa, r.ya,
		r.xb, r.yb, alive});
}
