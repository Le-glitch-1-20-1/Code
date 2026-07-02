/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_toolbar-2.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:04:52 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 22:55:23 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

static void	theme_btn_draw(Rectangle tr, t_color_theme ti, bool thov,
				char tt[48])
{
	if (thov)
		DrawRectangleRec(tr, ui_c_hover());
	else
		DrawRectangleRec(tr, ui_c_panel());
	if (thov)
		DrawRectangleLinesEx(tr, 1.0f, ui_c_hi());
	else
		DrawRectangleLinesEx(tr, 1.0f, ui_c_border());
	DrawCircle((int)(tr.x + tr.width / 2), (int)(tr.y + tr.height / 2),
		tr.width * 0.3f, ti.cell);
	if (thov)
		DrawCircleLines((int)(tr.x + tr.width / 2),
			(int)(tr.y + tr.height / 2), tr.width * 0.3f, ui_c_hi());
	else
		DrawCircleLines((int)(tr.x + tr.width / 2),
			(int)(tr.y + tr.height / 2), tr.width * 0.3f, ui_c_border());
	if (thov)
	{
		snprintf(tt, 48, "Theme: %s", ti.name);
		draw_tooltip(tr, tt);
	}
}

t_ui_action	toolbar_view_theme(int *x, t_toolbar_geom g, int theme_idx,
				t_ui_action act)
{
	t_color_theme	ti;
	Rectangle		tr;
	bool			thov;
	char			tt[48];

	if (theme_idx >= 0 && theme_idx < 5)
		ti = get_theme(theme_idx);
	else
		ti = get_theme(0);
	tr = (Rectangle){(float)*x, (float)g.pad, (float)g.bsz, (float)g.bsz};
	thov = CheckCollisionPointRec(GetMousePosition(), tr);
	theme_btn_draw(tr, ti, thov, tt);
	*x += g.bsz + g.pad;
	if (act == UI_ACTION_NONE && thov
		&& IsMouseButtonReleased(MOUSE_BUTTON_LEFT))
		return (UI_ACTION_NEXT_THEME);
	return (act);
}

t_ui_action	toolbar_view(int *x, int pad, int bsz, int theme_idx)
{
	t_ui_action		act;
	t_toolbar_geom	g;

	g = (t_toolbar_geom){pad, bsz};
	act = toolbar_center_btn(x, pad, bsz);
	DrawLine(*x + 3, pad + 2, *x + 3, pad + bsz - 2, ui_c_border());
	*x += 12;
	if (act == UI_ACTION_NONE && toolbar_btn(x, g, icon_grid, "Grille"))
		act = UI_ACTION_TOGGLE_GRID;
	if (act == UI_ACTION_NONE && toolbar_btn(x, g, icon_hud, "HUD"))
		act = UI_ACTION_TOGGLE_HUD;
	if (act == UI_ACTION_NONE && toolbar_btn(x, g, icon_chunk_debug,
			"Debug chunks"))
		act = UI_ACTION_TOGGLE_CHUNK_DEBUG;
	act = toolbar_view_theme(x, g, theme_idx, act);
	return (act);
}
