/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   config.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:11:16 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 07:27:23 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "config.h"

#include "main.h"

void	cfg_default_part1(t_key_config *cfg)
{
	cfg->pan_up = KEY_W;
	cfg->pan_down = KEY_S;
	cfg->pan_left = KEY_A;
	cfg->pan_right = KEY_D;
	cfg->toggle_play = KEY_SPACE;
	cfg->step_once = KEY_RIGHT;
	cfg->clear = KEY_X;
	cfg->clear_zone = KEY_X;
	cfg->center_view = KEY_F;
	cfg->random = KEY_Z;
	cfg->rotate = KEY_R;
}

void	cfg_default_part2(t_key_config *cfg)
{
	cfg->toggle_grid = KEY_G;
	cfg->toggle_hud = KEY_H;
	cfg->toggle_chunk_debug = KEY_TAB;
	cfg->next_theme = KEY_T;
	cfg->undo = KEY_Z;
	cfg->copy = KEY_C;
	cfg->paste = KEY_V;
	cfg->speed_up = KEY_UP;
	cfg->speed_down = KEY_DOWN;
	cfg->mod_save = KEY_LEFT_CONTROL;
	cfg->save = KEY_C;
	cfg->load = KEY_V;
}

t_key_config	cfg_default_move(void)
{
	t_key_config	cfg;

	cfg_default_part1(&cfg);
	cfg_default_part2(&cfg);
	return (cfg);
}

t_key_config	default_key_config(void)
{
	return (cfg_default_move());
}
