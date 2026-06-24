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

void	minmax_copy(t_app *app, int *xa, int *ya, int *xb, int *yb)
{
	if (app->copy_x0 < app->copy_x1)
		*xa = app->copy_x0;
	else
		*xa = app->copy_x1;
	if (app->copy_y0 < app->copy_y1)
		*ya = app->copy_y0;
	else
		*ya = app->copy_y1;
	if (app->copy_x0 > app->copy_x1)
		*xb = app->copy_x0;
	else
		*xb = app->copy_x1;
	if (app->copy_y0 > app->copy_y1)
		*yb = app->copy_y0;
	else
		*yb = app->copy_y1;
}

void	draw_selections_copy(t_app *app)
{
	int	xa;
	int	ya;
	int	xb;
	int	yb;

	if (!app->copy_select_mode)
		return ;
	if (!app->copy_select_drag)
	{
		draw_selection_info_box((t_sel_box){"Copier", 0, 0, -1, -1, 0});
		return ;
	}
	minmax_copy(app, &xa, &ya, &xb, &yb);
	draw_select_overlay(app, xa, ya, xb, yb, "Copier",
		(Color){50, 120, 220, 45}, (Color){80, 160, 255, 230});
}

void	draw_selections(t_app *app)
{
	draw_selections_clear(app);
	draw_selections_copy(app);
}
