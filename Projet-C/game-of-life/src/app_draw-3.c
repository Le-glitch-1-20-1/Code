/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_draw-3.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:07:41 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 11:28:48 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	minmax_copy(t_app *app, t_rect *out)
{
	if (app->copy_x0 < app->copy_x1)
		out->xa = app->copy_x0;
	else
		out->xa = app->copy_x1;
	if (app->copy_y0 < app->copy_y1)
		out->ya = app->copy_y0;
	else
		out->ya = app->copy_y1;
	if (app->copy_x0 > app->copy_x1)
		out->xb = app->copy_x0;
	else
		out->xb = app->copy_x1;
	if (app->copy_y0 > app->copy_y1)
		out->yb = app->copy_y0;
	else
		out->yb = app->copy_y1;
}

void	draw_selections_copy(t_app *app)
{
	t_rect	r;

	if (!app->copy_select_mode)
		return ;
	if (!app->copy_select_drag)
	{
		draw_selection_info_box((t_sel_box){"Copier", 0, 0, -1, -1, 0});
		return ;
	}
	minmax_copy(app, &r);
	draw_select_overlay(app, r, (t_overlay_style){"Copier",
		(Color){50, 120, 220, 45}, (Color){80, 160, 255, 230}});
}

void	draw_selections(t_app *app)
{
	draw_selections_clear(app);
	draw_selections_copy(app);
}
