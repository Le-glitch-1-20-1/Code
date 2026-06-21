/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_keybinds-1.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:20:27 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:20:01 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"
#include "ui_shared.h"
#include "config.h"
#include <stddef.h>
#include <string.h>

#define KB_N	28

const t_kb_entry	g_kb_table[] = {
{NULL, "Navigation", -1},
{"Deplacer vue - Haut", NULL, (int)offsetof(t_key_config, pan_up)},
{"Deplacer vue - Bas", NULL, (int)offsetof(t_key_config, pan_down)},
{"Deplacer vue - Gauche", NULL, (int)offsetof(t_key_config, pan_left)},
{"Deplacer vue - Droite", NULL, (int)offsetof(t_key_config, pan_right)},
{NULL, "Simulation", -1},
{"Play / Pause", NULL, (int)offsetof(t_key_config, toggle_play)},
{"Pas suivant", NULL, (int)offsetof(t_key_config, step_once)},
{"Effacer la grille", NULL, (int)offsetof(t_key_config, clear)},
{"Vitesse +", NULL, (int)offsetof(t_key_config, speed_up)},
{"Vitesse -", NULL, (int)offsetof(t_key_config, speed_down)},
{NULL, "Outils", -1},
{"Remplissage aleatoire", NULL, (int)offsetof(t_key_config, random)},
{"Rotation pattern", NULL, (int)offsetof(t_key_config, rotate)},
{"Annuler (Undo)", NULL, (int)offsetof(t_key_config, undo)},
{"Copier zone", NULL, (int)offsetof(t_key_config, copy)},
{"Effacer zone", NULL, (int)offsetof(t_key_config, clear_zone)},
{"Coller", NULL, (int)offsetof(t_key_config, paste)},
{NULL, "Vue", -1},
{"Centrer la vue", NULL, (int)offsetof(t_key_config, center_view)},
{"Grille on/off", NULL, (int)offsetof(t_key_config, toggle_grid)},
{"HUD on/off", NULL, (int)offsetof(t_key_config, toggle_hud)},
{"Debug chunks on/off", NULL,
	(int)offsetof(t_key_config, toggle_chunk_debug)},
{"Theme suivant", NULL, (int)offsetof(t_key_config, next_theme)},
{NULL, "Fichiers", -1},
{"Modificateur", NULL, (int)offsetof(t_key_config, mod_save)},
{"Sauvegarder zone", NULL, (int)offsetof(t_key_config, save)},
{"Charger RLE", NULL, (int)offsetof(t_key_config, load)},
};

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
	if (k == KEY_F1)
		return ("F1");
	if (k == KEY_F2)
		return ("F2");
	if (k == KEY_F3)
		return ("F3");
	if (k == KEY_F4)
		return ("F4");
	if (k == KEY_F5)
		return ("F5");
	if (k == KEY_F6)
		return ("F6");
	if (k == KEY_F7)
		return ("F7");
	if (k == KEY_F8)
		return ("F8");
	if (k == KEY_F9)
		return ("F9");
	if (k == KEY_F10)
		return ("F10");
	if (k == KEY_F11)
		return ("F11");
	if (k == KEY_F12)
		return ("F12");
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
