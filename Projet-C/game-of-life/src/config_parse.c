/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   config_parse.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:11:16 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 09:12:02 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "config.h"

void	cfg_parse_line(t_key_config *cfg, char *key, int val)
{
	if (!strcmp(key, "pan_up"))
		cfg->pan_up = val;
	else if (!strcmp(key, "pan_down"))
		cfg->pan_down = val;
	else if (!strcmp(key, "pan_left"))
		cfg->pan_left = val;
	else if (!strcmp(key, "pan_right"))
		cfg->pan_right = val;
	else if (!strcmp(key, "toggle_play"))
		cfg->toggle_play = val;
	else if (!strcmp(key, "step_once"))
		cfg->step_once = val;
	else if (!strcmp(key, "clear"))
		cfg->clear = val;
	else if (!strcmp(key, "clear_zone"))
		cfg->clear_zone = val;
	else if (!strcmp(key, "center_view"))
		cfg->center_view = val;
	else if (!strcmp(key, "random"))
		cfg->random = val;
	else if (!strcmp(key, "rotate"))
		cfg->rotate = val;
}

void	cfg_parse_line2(t_key_config *cfg, char *key, int val)
{
	if (!strcmp(key, "toggle_grid"))
		cfg->toggle_grid = val;
	else if (!strcmp(key, "toggle_hud"))
		cfg->toggle_hud = val;
	else if (!strcmp(key, "toggle_chunk_debug"))
		cfg->toggle_chunk_debug = val;
	else if (!strcmp(key, "next_theme"))
		cfg->next_theme = val;
	else if (!strcmp(key, "undo"))
		cfg->undo = val;
	else if (!strcmp(key, "copy"))
		cfg->copy = val;
	else if (!strcmp(key, "paste"))
		cfg->paste = val;
	else if (!strcmp(key, "speed_up"))
		cfg->speed_up = val;
	else if (!strcmp(key, "speed_down"))
		cfg->speed_down = val;
	else if (!strcmp(key, "mod_save"))
		cfg->mod_save = val;
	else if (!strcmp(key, "save"))
		cfg->save = val;
	else if (!strcmp(key, "load"))
		cfg->load = val;
}
