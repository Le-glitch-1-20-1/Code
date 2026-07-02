/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_toolbar-1.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:06:59 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 09:18:55 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

static void	toolbar_sim_icon(bool running, t_icon_draw *ic, const char **tip)
{
	if (running)
	{
		*ic = icon_pause;
		*tip = "Pause";
	}
	else
	{
		*ic = icon_play;
		*tip = "Play";
	}
}

bool	toolbar_btn(int *x, t_toolbar_geom g, t_icon_draw ic,
			const char *tip)
{
	bool	clicked;
	int		px;

	px = *x;
	clicked = (icon_button((Rectangle){px, g.pad, g.bsz, g.bsz}, ic, tip,
				false) == BTN_CLICKED);
	*x += g.bsz + g.pad;
	return (clicked);
}

t_ui_action	toolbar_sim(int *x, int pad, int bsz, bool running)
{
	t_ui_action		act;
	t_icon_draw		ic;
	const char		*tip;
	t_toolbar_geom	g;

	g = (t_toolbar_geom){pad, bsz};
	act = UI_ACTION_NONE;
	toolbar_sim_icon(running, &ic, &tip);
	if (toolbar_btn(x, g, ic, tip))
		act = UI_ACTION_PLAY;
	if (act == UI_ACTION_NONE && toolbar_btn(x, g, icon_step, "Pas suivant"))
		act = UI_ACTION_STEP;
	if (act == UI_ACTION_NONE && toolbar_btn(x, g, icon_clear,
			"Effacer grille"))
		act = UI_ACTION_CLEAR;
	if (act == UI_ACTION_NONE && toolbar_btn(x, g, icon_undo, "Annuler"))
		act = UI_ACTION_UNDO;
	return (act);
}

t_ui_action	toolbar_files(int *x, int pad, int bsz)
{
	t_ui_action		act;
	t_toolbar_geom	g;

	g = (t_toolbar_geom){pad, bsz};
	act = UI_ACTION_NONE;
	DrawLine(*x + 3, pad + 2, *x + 3, pad + bsz - 2, ui_c_border());
	*x += 12;
	if (toolbar_btn(x, g, icon_save, "Sauvegarder"))
		act = UI_ACTION_OPEN_SAVE;
	if (act == UI_ACTION_NONE && toolbar_btn(x, g, icon_load, "Charger RLE"))
		act = UI_ACTION_OPEN_LOAD;
	return (act);
}
