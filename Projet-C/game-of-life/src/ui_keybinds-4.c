/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_keybinds-3b.c                                   :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:04:34 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 23:05:57 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

static Rectangle	kb_panel_rect(void)
{
	int	ph;
	int	pw;

	ph = GetScreenHeight() - 80;
	if (ph > 680)
		ph = 680;
	if (ph < 300)
		ph = 300;
	pw = 560;
	return ((Rectangle){(GetScreenWidth() - pw) / 2.0f,
		(GetScreenHeight() - ph) / 2.0f, (float)pw, (float)ph});
}

static t_kb_view	kb_view_from_panel(Rectangle p)
{
	t_kb_view	v;

	v.list_x = (int)p.x + 14;
	v.list_top = (int)p.y + 50;
	v.list_bot = (int)p.y + (int)p.height - 48;
	v.list_w = (int)p.width - 28;
	return (v);
}

static void	kb_draw_header(Rectangle p)
{
	panel_draw(p, C_PANEL, C_HI);
	text_c("CONFIGURATION DES TOUCHES", FM, (Vector2){p.x + p.width / 2.0f,
		p.y + 22}, C_HI);
	DrawLine((int)p.x + 10, (int)p.y + 42,
		(int)p.x + p.width - 10, (int)p.y + 42, C_BORDER);
}

bool	ui_draw_keybinds(t_key_config *cfg)
{
	static int	scroll_px = 0;
	static int	wait_idx = -1;
	t_kb_view	v;
	Rectangle	p;
	int			lh;

	overlay();
	p = kb_panel_rect();
	kb_draw_header(p);
	v = kb_view_from_panel(p);
	lh = v.list_bot - v.list_top;
	scroll_px = kb_scroll(p, scroll_px, kb_total_h(), lh);
	if (wait_idx >= 0)
		wait_idx = kb_capture(cfg, wait_idx);
	BeginScissorMode(v.list_x, v.list_top, v.list_w, lh);
	kb_draw_list(v, scroll_px, wait_idx, cfg);
	EndScissorMode();
	kb_draw_scrollbar(v, lh, kb_total_h(), scroll_px);
	if (ui_button((Rectangle){p.x + p.width / 2.0f - 65, p.y + p.height - 40,
			130, 32}, "Retour", false) == BTN_CLICKED
		|| IsKeyPressed(KEY_ESCAPE))
	{
		wait_idx = -1;
		scroll_px = 0;
		return (true);
	}
	return (false);
}
