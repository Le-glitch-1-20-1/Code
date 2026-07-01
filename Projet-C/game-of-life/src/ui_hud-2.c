/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_hud-2.c                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/27 12:00:00 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 12:00:00 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

void	ui_draw_message(const char *msg, float timer)
{
	int		mw;
	int		top;
	float	a;

	if (timer <= 0.0f || !msg[0])
		return ;
	if (timer > 0.5f)
		a = 1.0f;
	else
		a = timer / 0.5f;
	mw = MeasureText(msg, FS) + 20;
	top = 44;
	DrawRectangle(10, top, mw, 26,
		(Color){0, 0, 0, (unsigned char)(a * 160)});
	DrawRectangleLinesEx((Rectangle){10, top, mw, 26}, 1.0f,
		(Color){127, 119, 221, (unsigned char)(a * 180)});
	DrawText(msg, 20, top + (26 - FS) / 2, FS,
		(Color){220, 220, 230, (unsigned char)(a * 240)});
}
