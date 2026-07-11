/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_keybinds-5.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/11 00:00:00 by le-glitch         #+#    #+#             */
/*   Updated: 2026/07/11 11:00:27 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

void	kb_table_fill_1(t_kb_entry *t)
{
	t[0] = (t_kb_entry){NULL, "Navigation", -1};
	t[1] = (t_kb_entry){"Deplacer vue - Haut", NULL,
		(int)offsetof(t_key_config, pan_up)};
	t[2] = (t_kb_entry){"Deplacer vue - Bas", NULL,
		(int)offsetof(t_key_config, pan_down)};
	t[3] = (t_kb_entry){"Deplacer vue - Gauche", NULL,
		(int)offsetof(t_key_config, pan_left)};
	t[4] = (t_kb_entry){"Deplacer vue - Droite", NULL,
		(int)offsetof(t_key_config, pan_right)};
	t[5] = (t_kb_entry){NULL, "Simulation", -1};
	t[6] = (t_kb_entry){"Play / Pause", NULL,
		(int)offsetof(t_key_config, toggle_play)};
	t[7] = (t_kb_entry){"Pas suivant", NULL,
		(int)offsetof(t_key_config, step_once)};
	t[8] = (t_kb_entry){"Effacer la grille", NULL,
		(int)offsetof(t_key_config, clear)};
	t[9] = (t_kb_entry){"Vitesse +", NULL,
		(int)offsetof(t_key_config, speed_up)};
}

void	kb_table_fill_2(t_kb_entry *t)
{
	t[10] = (t_kb_entry){"Vitesse -", NULL,
		(int)offsetof(t_key_config, speed_down)};
	t[11] = (t_kb_entry){NULL, "Outils", -1};
	t[12] = (t_kb_entry){"Remplissage aleatoire", NULL,
		(int)offsetof(t_key_config, random)};
	t[13] = (t_kb_entry){"Rotation pattern", NULL,
		(int)offsetof(t_key_config, rotate)};
	t[14] = (t_kb_entry){"Annuler (Undo)", NULL,
		(int)offsetof(t_key_config, undo)};
	t[15] = (t_kb_entry){"Copier zone", NULL,
		(int)offsetof(t_key_config, copy)};
	t[16] = (t_kb_entry){"Effacer zone", NULL,
		(int)offsetof(t_key_config, clear_zone)};
	t[17] = (t_kb_entry){"Coller", NULL,
		(int)offsetof(t_key_config, paste)};
	t[18] = (t_kb_entry){NULL, "Vue", -1};
	t[19] = (t_kb_entry){"Centrer la vue", NULL,
		(int)offsetof(t_key_config, center_view)};
}

void	kb_table_fill_3(t_kb_entry *t)
{
	t[20] = (t_kb_entry){"Grille on/off", NULL,
		(int)offsetof(t_key_config, toggle_grid)};
	t[21] = (t_kb_entry){"HUD on/off", NULL,
		(int)offsetof(t_key_config, toggle_hud)};
	t[22] = (t_kb_entry){"Debug chunks on/off", NULL,
		(int)offsetof(t_key_config, toggle_chunk_debug)};
	t[23] = (t_kb_entry){"Theme suivant", NULL,
		(int)offsetof(t_key_config, next_theme)};
	t[24] = (t_kb_entry){NULL, "Fichiers", -1};
	t[25] = (t_kb_entry){"Modificateur", NULL,
		(int)offsetof(t_key_config, mod_save)};
	t[26] = (t_kb_entry){"Sauvegarder zone", NULL,
		(int)offsetof(t_key_config, save)};
	t[27] = (t_kb_entry){"Charger RLE", NULL,
		(int)offsetof(t_key_config, load)};
}

const t_kb_entry	*kb_table(void)
{
	static t_kb_entry	table[KB_N];
	static bool			ready = false;

	if (!ready)
	{
		kb_table_fill_1(table);
		kb_table_fill_2(table);
		kb_table_fill_3(table);
		ready = true;
	}
	return (table);
}

t_kb_entry	kb_entry(int idx)
{
	return (kb_table()[idx]);
}
