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

t_ui_action	toolbar_sim(int *x, int pad, int bsz, bool running)
{
	t_ui_action		act;
	t_icon_draw		ic;
	const char		*tip;
	int				rx;

	act = UI_ACTION_NONE;
	if (running)
	{
		ic = icon_pause;
		tip = "Pause";
	}
	else
	{
		ic = icon_play;
		tip = "Play";
	}
	rx = *x;
	if (icon_button((Rectangle){rx, pad, bsz, bsz}, ic, tip,
		false) == BTN_CLICKED)
		act = UI_ACTION_PLAY;
	*x += bsz + pad;
	rx = *x;
	if (act == UI_ACTION_NONE && icon_button((Rectangle){rx, pad, bsz, bsz},
		icon_step, "Pas suivant", false) == BTN_CLICKED)
		act = UI_ACTION_STEP;
	*x += bsz + pad;
	rx = *x;
	if (act == UI_ACTION_NONE && icon_button((Rectangle){rx, pad, bsz, bsz},
		icon_clear, "Effacer grille", false) == BTN_CLICKED)
		act = UI_ACTION_CLEAR;
	*x += bsz + pad;
	rx = *x;
	if (act == UI_ACTION_NONE && icon_button((Rectangle){rx, pad, bsz, bsz},
		icon_undo, "Annuler", false) == BTN_CLICKED)
		act = UI_ACTION_UNDO;
	*x += bsz + pad;
	return (act);
}

t_ui_action	toolbar_files(int *x, int pad, int bsz)
{
	t_ui_action	act;
	int			rx;

	act = UI_ACTION_NONE;
	DrawLine(*x + 3, pad + 2, *x + 3, pad + bsz - 2, C_BORDER);
	*x += 12;
	rx = *x;
	if (icon_button((Rectangle){rx, pad, bsz, bsz},
		icon_save, "Sauvegarder", false) == BTN_CLICKED)
		act = UI_ACTION_OPEN_SAVE;
	*x += bsz + pad;
	rx = *x;
	if (act == UI_ACTION_NONE && icon_button((Rectangle){rx, pad, bsz, bsz},
		icon_load, "Charger RLE", false) == BTN_CLICKED)
		act = UI_ACTION_OPEN_LOAD;
	*x += bsz + pad;
	return (act);
}

t_ui_action	toolbar_tools(int *x, int pad, int bsz)
{
	t_ui_action	act;
	int			rx;

	act = UI_ACTION_NONE;
	DrawLine(*x + 3, pad + 2, *x + 3, pad + bsz - 2, C_BORDER);
	*x += 12;
	rx = *x;
	if (icon_button((Rectangle){rx, pad, bsz, bsz},
		icon_random, "Aleatoire", false) == BTN_CLICKED)
		act = UI_ACTION_RANDOM;
	*x += bsz + pad;
	rx = *x;
	if (act == UI_ACTION_NONE && icon_button((Rectangle){rx, pad, bsz, bsz},
		icon_copy, "Copier zone", false) == BTN_CLICKED)
		act = UI_ACTION_COPY_ZONE;
	*x += bsz + pad;
	rx = *x;
	if (act == UI_ACTION_NONE && icon_button((Rectangle){rx, pad, bsz, bsz},
		icon_paste, "Coller", false) == BTN_CLICKED)
		act = UI_ACTION_PASTE;
	*x += bsz + pad;
	rx = *x;
	if (act == UI_ACTION_NONE && icon_button((Rectangle){rx, pad, bsz, bsz},
		icon_clear_zone, "Effacer zone", false) == BTN_CLICKED)
		act = UI_ACTION_CLEAR_ZONE;
	*x += bsz + pad;
	return (act);
}

t_ui_action	toolbar_center_btn(int *x, int pad, int bsz)
{
	Rectangle	rb;
	Vector2		m2;
	bool		hov2;
	bool		click2;
	float		r2;
	float		cx2;
	float		cy2;

	rb = (Rectangle){(float)*x, (float)pad, (float)bsz, (float)bsz};
	m2 = GetMousePosition();
	hov2 = CheckCollisionPointRec(m2, rb);
	click2 = hov2 && IsMouseButtonReleased(MOUSE_BUTTON_LEFT);
	if (hov2 && IsMouseButtonDown(0))
		DrawRectangleRec(rb, C_ACTIVE);
	else if (hov2)
		DrawRectangleRec(rb, C_HOVER);
	else
		DrawRectangleRec(rb, C_PANEL);
	if (hov2)
		DrawRectangleLinesEx(rb, 1.0f, C_HI);
	else
		DrawRectangleLinesEx(rb, 1.0f, C_BORDER);
	r2 = rb.width * 0.35f * 0.8f;
	cx2 = rb.x + rb.width / 2;
	cy2 = rb.y + rb.height / 2;
	if (hov2)
		DrawLineEx((Vector2){cx2 - r2, cy2},
			(Vector2){cx2 + r2, cy2}, 1.5f, C_HI);
	else
		DrawLineEx((Vector2){cx2 - r2, cy2},
			(Vector2){cx2 + r2, cy2}, 1.5f, C_TEXT);
	if (hov2)
		DrawLineEx((Vector2){cx2, cy2 - r2},
			(Vector2){cx2, cy2 + r2}, 1.5f, C_HI);
	else
		DrawLineEx((Vector2){cx2, cy2 - r2},
			(Vector2){cx2, cy2 + r2}, 1.5f, C_TEXT);
	if (hov2)
		DrawCircleLines((int)cx2, (int)cy2, (int)(r2 * 0.6f), C_HI);
	else
		DrawCircleLines((int)cx2, (int)cy2, (int)(r2 * 0.6f), C_TEXT);
	if (hov2)
		draw_tooltip(rb, "Recentrer");
	*x += bsz + pad;
	if (click2)
		return (UI_ACTION_CENTER);
	return (UI_ACTION_NONE);
}
