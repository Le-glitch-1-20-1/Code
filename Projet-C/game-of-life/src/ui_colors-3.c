/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_colors-3.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/27 21:05:20 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 21:05:20 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

Color	ui_c_yellow(void)
{
	return ((Color){230, 185, 55, 255});
}

Color	ui_c_red(void)
{
	return ((Color){210, 72, 72, 255});
}

Color	ui_c_overlay(void)
{
	return ((Color){0, 0, 0, 195});
}

Color	ui_c_accent2(void)
{
	return ((Color){80, 195, 145, 255});
}

Color	ui_c_orange(void)
{
	return ((Color){220, 140, 50, 255});
}
