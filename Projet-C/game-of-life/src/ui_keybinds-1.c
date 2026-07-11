/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_keybinds-1.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:20:27 by le-glitch         #+#    #+#             */
/*   Updated: 2026/07/11 10:58:55 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

int	*kb_field(t_key_config *cfg, int offset)
{
	return ((int *)((char *)cfg + offset));
}

const char	*kname_mod(int k)
{
	if (k == KEY_SPACE)
		return ("ESPACE");
	if (k == KEY_ESCAPE)
		return ("ECHAP");
	if (k == KEY_ENTER)
		return ("ENTREE");
	if (k == KEY_TAB)
		return ("TAB");
	if (k == KEY_BACKSPACE)
		return ("SUPPR");
	if (k == KEY_LEFT_CONTROL)
		return ("CTRL-G");
	if (k == KEY_RIGHT_CONTROL)
		return ("CTRL-D");
	if (k == KEY_LEFT_SHIFT)
		return ("MAJ-G");
	if (k == KEY_RIGHT_SHIFT)
		return ("MAJ-D");
	if (k == KEY_LEFT_ALT)
		return ("ALT-G");
	if (k == KEY_RIGHT_ALT)
		return ("ALT-D");
	return (NULL);
}

const char	*kname_arrow(int k)
{
	if (k == KEY_UP)
		return ("HAUT");
	if (k == KEY_DOWN)
		return ("BAS");
	if (k == KEY_LEFT)
		return ("GAUCHE");
	if (k == KEY_RIGHT)
		return ("DROITE");
	return (NULL);
}

const char	*kname_fn(int k, char *buf)
{
	static const char	*names[] = {"F1", "F2", "F3", "F4", "F5", "F6",
		"F7", "F8", "F9", "F10", "F11", "F12"};
	int					i;

	if (k >= KEY_F1 && k <= KEY_F12)
	{
		i = k - KEY_F1;
		return (names[i]);
	}
	snprintf(buf, 16, "#%d", k);
	return (buf);
}

const char	*kname(int k)
{
	static char		buf[16];
	const char		*r;

	if (k >= KEY_A && k <= KEY_Z)
	{
		buf[0] = 'A' + (k - KEY_A);
		buf[1] = 0;
		return (buf);
	}
	if (k >= KEY_ZERO && k <= KEY_NINE)
	{
		snprintf(buf, 16, "%d", k - KEY_ZERO);
		return (buf);
	}
	r = kname_mod(k);
	if (r)
		return (r);
	r = kname_arrow(k);
	if (r)
		return (r);
	return (kname_fn(k, buf));
}
