/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_savezone-4.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/27 21:05:20 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 21:05:20 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

static bool	sz_phase1_save(t_save_zone_state *sz, char *out_path,
				int path_len, bool *editing)
{
	const char	*nm;

	if (sz->name_buf[0])
		nm = sz->name_buf;
	else
		nm = "mon_pattern";
	snprintf(out_path, path_len, "assets/patterns/%s.rle", nm);
	*editing = false;
	return (true);
}

bool	sz_phase1(t_save_zone_state *sz, char *out_path, int path_len)
{
	static bool	editing = false;
	Rectangle	p;
	int			pw;
	int			ph;

	pw = 480;
	ph = 230;
	overlay();
	p = (Rectangle){(GetScreenWidth() - pw) / 2.0f,
		(GetScreenHeight() - ph) / 2.0f, pw, ph};
	panel_draw(p, ui_c_panel(), ui_c_hi());
	sz_draw_info(sz, p, pw);
	sz_draw_namefield(sz, p, pw, &editing);
	if (ui_button((Rectangle){p.x + 24, p.y + ph - 46, 160, 34},
		"Sauvegarder", false) == BTN_CLICKED
		|| (editing && IsKeyPressed(KEY_ENTER)))
		return (sz_phase1_save(sz, out_path, path_len, &editing));
	if (ui_button((Rectangle){p.x + pw - 184, p.y + ph - 46, 160, 34},
		"Annuler", false) == BTN_CLICKED || IsKeyPressed(KEY_ESCAPE))
	{
		editing = false;
		sz->cancelled = true;
	}
	return (false);
}

bool	ui_draw_save_zone(t_save_zone_state *sz, t_camera2d_gol cam,
		char *out_path, int path_len)
{
	if (sz->phase == 0)
	{
		sz_phase0_input(sz, cam);
		sz_phase0_draw(sz, cam);
		if (IsKeyPressed(KEY_ESCAPE))
			sz->cancelled = true;
		return (false);
	}
	return (sz_phase1(sz, out_path, path_len));
}
