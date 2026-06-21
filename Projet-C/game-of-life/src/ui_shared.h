/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_shared.h                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:15:38 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:20:05 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef UI_SHARED_H
# define UI_SHARED_H

# include "raylib.h"
# include <stdbool.h>

# define C_BG		(Color){14,  14,  18,  255}
# define C_PANEL	(Color){24,  24,  34,  245}
# define C_PANEL2	(Color){30,  30,  44,  255}
# define C_BORDER	(Color){55,  55,  80,  255}
# define C_HI		(Color){127, 119, 221, 255}
# define C_TEXT		(Color){210, 210, 225, 255}
# define C_DIM		(Color){100, 100, 125, 255}
# define C_HOVER	(Color){42,  40,  68,  255}
# define C_ACTIVE	(Color){72,  66,  148, 255}
# define C_GREEN	(Color){72,  200, 120, 255}
# define C_YELLOW	(Color){230, 185, 55,  255}
# define C_RED		(Color){210, 72,  72,  255}
# define C_OVERLAY	(Color){0,   0,   0,   195}
# define C_ACCENT2	(Color){80,  195, 145, 255}
# define C_ORANGE	(Color){220, 140, 50,  255}

# define FS		15
# define FM		18
# define FL		24
# define FXL	32

void	panel_draw(Rectangle r, Color bg, Color border);
void	text_c(const char *t, int fs, float cx, float cy, Color c);
void	overlay(void);
void	draw_tooltip(Rectangle rect, const char *tooltip);

#endif
