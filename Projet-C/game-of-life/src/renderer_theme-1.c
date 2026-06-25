/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   renderer_theme-1.c                                 :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:24:24 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 11:06:45 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "renderer.h"

void	theme_violet(t_color_theme *t)
{
	t->name = "Violet";
	t->bg = (Color){14, 18, 20, 255};
	t->cell = (Color){127, 119, 221, 255};
	t->grid = (Color){35, 35, 40, 255};
}

void	theme_vert(t_color_theme *t)
{
	t->name = "Vert";
	t->bg = (Color){10, 18, 14, 255};
	t->cell = (Color){72, 200, 120, 255};
	t->grid = (Color){25, 40, 30, 255};
}

void	theme_ambre(t_color_theme *t)
{
	t->name = "Ambre";
	t->bg = (Color){18, 14, 8, 255};
	t->cell = (Color){230, 160, 40, 255};
	t->grid = (Color){40, 35, 20, 255};
}

void	theme_cyan(t_color_theme *t)
{
	t->name = "Cyan";
	t->bg = (Color){8, 16, 20, 255};
	t->cell = (Color){60, 200, 210, 255};
	t->grid = (Color){20, 35, 42, 255};
}
