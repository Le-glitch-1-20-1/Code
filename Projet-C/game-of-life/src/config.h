/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   config.h                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:11:16 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 07:18:17 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef CONFIG_H
# define CONFIG_H

# include "main.h"

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


t_key_config	load_key_config(const char *path);
t_key_config	cfg_default_move(void);
t_key_config	default_key_config(void);

void			cfg_default_part1(t_key_config *cfg);
void			cfg_default_part2(t_key_config *cfg);
void			cfg_parse_line(t_key_config *cfg, char *key, int val);
void			cfg_parse_line2(t_key_config *cfg, char *key, int val);
void			save_key_config(const char *path, const t_key_config *cfg);

#endif
