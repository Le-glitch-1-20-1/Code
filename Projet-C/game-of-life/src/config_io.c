/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   config_io.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:11:16 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 07:27:15 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "config.h"

#include "main.h"

t_key_config	load_key_config(const char *path)
{
	t_key_config	cfg;
	FILE			*f;
	char			key[64];
	int				val;

	cfg = default_key_config();
	f = fopen(path, "r");
	if (!f)
		return (cfg);
	while (fscanf(f, " %63[^=]=%d", key, &val) == 2)
	{
		cfg_parse_line(&cfg, key, val);
		cfg_parse_line2(&cfg, key, val);
	}
	fclose(f);
	return (cfg);
}

void	save_key_config(const char *path, const t_key_config *cfg)
{
	FILE	*f;

	f = fopen(path, "w");
	if (!f)
		return ;
	fprintf(f,
		"pan_up=%d\npan_down=%d\npan_left=%d\npan_right=%d\n"
		"toggle_play=%d\nstep_once=%d\nclear=%d\nclear_zone=%d\n"
		"center_view=%d\nrandom=%d\nrotate=%d\ntoggle_grid=%d\n"
		"toggle_hud=%d\ntoggle_chunk_debug=%d\nnext_theme=%d\n"
		"undo=%d\ncopy=%d\npaste=%d\nspeed_up=%d\nspeed_down=%d\n"
		"mod_save=%d\nsave=%d\nload=%d\n",
		cfg->pan_up, cfg->pan_down, cfg->pan_left, cfg->pan_right,
		cfg->toggle_play, cfg->step_once, cfg->clear, cfg->clear_zone,
		cfg->center_view, cfg->random, cfg->rotate, cfg->toggle_grid,
		cfg->toggle_hud, cfg->toggle_chunk_debug, cfg->next_theme,
		cfg->undo, cfg->copy, cfg->paste, cfg->speed_up, cfg->speed_down,
		cfg->mod_save, cfg->save, cfg->load);
	fclose(f);
}
