/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_icons.h                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:03:51 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:03:54 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef UI_ICONS_H
# define UI_ICONS_H

# include "raylib.h"

typedef void	(*t_icon_draw)(float cx, float cy, float r, Color c);

void		icon_play(float cx, float cy, float r, Color c);
void		icon_pause(float cx, float cy, float r, Color c);
void		icon_step(float cx, float cy, float r, Color c);
void		icon_clear(float cx, float cy, float r, Color c);
void		icon_save(float cx, float cy, float r, Color c);
void		icon_load(float cx, float cy, float r, Color c);
void		icon_random(float cx, float cy, float r, Color c);
void		icon_menu(float cx, float cy, float r, Color c);
void		icon_grid(float cx, float cy, float r, Color c);
void		icon_hud(float cx, float cy, float r, Color c);
void		icon_chunk_debug(float cx, float cy, float r, Color c);
void		icon_undo(float cx, float cy, float r, Color c);
void		icon_copy(float cx, float cy, float r, Color c);
void		icon_clear_zone(float cx, float cy, float r, Color c);
void		icon_paste(float cx, float cy, float r, Color c);

t_btn_state	icon_button(Rectangle rect, t_icon_draw draw_fn,
				const char *tooltip, bool active);

#endif
