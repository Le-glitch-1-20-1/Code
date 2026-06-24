/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   renderer_theme-2.c                                 :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:24:24 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 23:06:42 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "renderer.h"

void	theme_blanc(t_color_theme *t)
{
	t->name = "Blanc";
	t->bg = (Color){20, 20, 26, 255};
	t->cell = (Color){210, 210, 220, 255};
	t->grid = (Color){38, 38, 48, 255};
}

t_color_theme	get_theme(int idx)
{
	t_color_theme	t;

	if (idx == 0)
		theme_violet(&t);
	else if (idx == 1)
		theme_vert(&t);
	else if (idx == 2)
		theme_ambre(&t);
	else if (idx == 3)
		theme_cyan(&t);
	else
		theme_blanc(&t);
	return (t);
}
