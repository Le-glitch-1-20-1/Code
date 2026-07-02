/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_colors-2.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/27 21:05:20 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 21:05:20 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

Color	ui_c_text(void)
{
	return ((Color){210, 210, 225, 255});
}

Color	ui_c_dim(void)
{
	return ((Color){100, 100, 125, 255});
}

Color	ui_c_hover(void)
{
	return ((Color){42, 40, 68, 255});
}

Color	ui_c_active(void)
{
	return ((Color){72, 66, 148, 255});
}

Color	ui_c_green(void)
{
	return ((Color){72, 200, 120, 255});
}
