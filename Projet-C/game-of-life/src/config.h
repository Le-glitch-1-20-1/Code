/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   config.h                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:11:16 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/21 23:19:30 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef CONFIG_H
# define CONFIG_H

# include <stdio.h>
# include <string.h>
# include "raylib.h"

/*
** Sur un clavier AZERTY, raylib rapporte Z comme KEY_W et Q comme KEY_A.
** Les defauts ici utilisent KEY_W / KEY_A pour que Z/Q fonctionnent
** nativement.
*/
typedef struct s_key_config
{
	int	pan_up;
	int	pan_down;
	int	pan_left;
	int	pan_right;
	int	toggle_play;
	int	step_once;
	int	clear;
	int	clear_zone;
	int	center_view;
	int	random;
	int	rotate;
	int	toggle_grid;
	int	toggle_hud;
	int	toggle_chunk_debug;
	int	next_theme;
	int	undo;
	int	copy;
	int	paste;
	int	speed_up;
	int	speed_down;
	int	mod_save;
	int	save;
	int	load;
}	t_key_config;

static inline t_key_config	cfg_default_move(void)
{
	t_key_config	cfg;

	cfg.pan_up = KEY_W;
	cfg.pan_down = KEY_S;
	cfg.pan_left = KEY_A;
	cfg.pan_right = KEY_D;
	cfg.toggle_play = KEY_SPACE;
	cfg.step_once = KEY_RIGHT;
	cfg.clear = KEY_X;
	cfg.clear_zone = KEY_X;
	cfg.center_view = KEY_F;
	cfg.random = KEY_Z;
	cfg.rotate = KEY_R;
	cfg.toggle_grid = KEY_G;
	cfg.toggle_hud = KEY_H;
	cfg.toggle_chunk_debug = KEY_TAB;
	cfg.next_theme = KEY_T;
	cfg.undo = KEY_Z;
	cfg.copy = KEY_C;
	cfg.paste = KEY_V;
	cfg.speed_up = KEY_UP;
	cfg.speed_down = KEY_DOWN;
	cfg.mod_save = KEY_LEFT_CONTROL;
	cfg.save = KEY_C;
	cfg.load = KEY_V;
	return (cfg);
}

static inline t_key_config	default_key_config(void)
{
	return (cfg_default_move());
}

static inline void	cfg_parse_line(t_key_config *cfg, char *key, int val)
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

static inline void	cfg_parse_line2(t_key_config *cfg, char *key, int val)
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

static inline t_key_config	load_key_config(const char *path)
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

static inline void	save_key_config(const char *path, const t_key_config *cfg)
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

#endif
