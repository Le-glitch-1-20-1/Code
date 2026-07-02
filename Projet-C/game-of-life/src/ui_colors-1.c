/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_colors-1.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/27 21:05:20 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 21:05:20 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

Color	ui_c_bg(void)
{
	return ((Color){14, 14, 18, 255});
}

Color	ui_c_panel(void)
{
	return ((Color){24, 24, 34, 245});
}

Color	ui_c_panel2(void)
{
	return ((Color){30, 30, 44, 255});
}

Color	ui_c_border(void)
{
	return ((Color){55, 55, 80, 255});
}

Color	ui_c_hi(void)
{
	return ((Color){127, 119, 221, 255});
}
