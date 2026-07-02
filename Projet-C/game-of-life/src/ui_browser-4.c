/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_browser-4.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:05:17 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/25 08:33:22 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

t_browser_view	browser_layout(void)
{
	t_browser_view	v;
	int				sw;
	int				sh;

	sw = GetScreenWidth();
	sh = GetScreenHeight();
	v.pw = 970;
	if (sh - 80 < 580)
		v.ph = sh - 80;
	else
		v.ph = 580;
	v.p = (Rectangle){(sw - v.pw) / 2.0f, (sh - v.ph) / 2.0f,
		(float)v.pw, (float)v.ph};
	v.list_top = (int)v.p.y + 82;
	v.list_bot = (int)v.p.y + v.ph - 50;
	return (v);
}

void	draw_no_results(t_browser_view v, int fcount, int count)
{
	if (fcount == 0 && count == 0)
	{
		text_c("Aucun fichier .rle trouve.", FS, (Vector2){
			v.p.x + (v.pw - 530) / 2 + 16, v.p.y + v.ph / 2}, ui_c_dim());
		text_c("Placez vos .rle dans assets/patterns/", FS - 2,
			(Vector2){v.p.x + (v.pw - 530) / 2 + 16,
			v.p.y + v.ph / 2 + 22}, ui_c_dim());
	}
	else if (fcount == 0)
		text_c("Aucun resultat.", FS, (Vector2){
			v.p.x + (v.pw - 530) / 2 + 16, v.p.y + v.ph / 2}, ui_c_dim());
}

void	reset_browser_state(int *count, int *scroll, char *search,
			bool *search_edit)
{
	*count = -1;
	*scroll = 0;
	search[0] = 0;
	*search_edit = false;
}

void	draw_browser_header(t_browser_view v)
{
	panel_draw(v.p, ui_c_panel(), ui_c_hi());
	text_c("CHARGER UN PATTERN", FL, (Vector2){v.p.x + v.pw / 2,
		v.p.y + 26}, ui_c_hi());
	DrawLine((int)v.p.x + 10, (int)v.p.y + 48,
		(int)v.p.x + v.pw - 10, (int)v.p.y + 48, ui_c_border());
}
