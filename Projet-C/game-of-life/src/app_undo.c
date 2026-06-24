/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   app_undo.c                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:17:39 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/24 22:46:31 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "app.h"

void	push_undo(t_app *app)
{
	int	slot;

	slot = app->undo_head;
	if (app->undo_valid[slot])
	{
		map_free(&app->undo_stack[slot]);
		app->undo_valid[slot] = false;
	}
	map_init(&app->undo_stack[slot]);
	map_copy(&app->undo_stack[slot], &app->map);
	app->undo_valid[slot] = true;
	app->undo_head = (app->undo_head + 1) % UNDO_LEN;
	if (app->undo_count < UNDO_LEN)
		app->undo_count++;
}

void	pop_undo(t_app *app)
{
	int	slot;

	if (app->undo_count == 0)
		return ;
	app->undo_head = (app->undo_head - 1 + UNDO_LEN) % UNDO_LEN;
	app->undo_count--;
	slot = app->undo_head;
	if (!app->undo_valid[slot])
		return ;
	map_free(&app->map);
	app->map = app->undo_stack[slot];
	app->undo_valid[slot] = false;
	map_remove_dead(&app->map);
}
