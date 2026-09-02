/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   libs.c                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 17:58:58 by le-glitch         #+#    #+#             */
/*   Updated: 2026/09/02 20:39:23 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "makefile_generator.h"

static const t_lib	*get_libraries(size_t *nb)
{
	static const t_lib	libraries[] = {
	{
		"raylib", "raylib.h",
		"$(shell pkg-config --libs raylib 2>/dev/null || echo \"-lraylib\")"
		" -lm -lpthread -ldl -lrt -lX11",
		"-I/home/le-glitch/raylib/raylib-windows/src",
		"-L/home/le-glitch/raylib/raylib-windows/src",
		"-lraylib -lopengl32 -lgdi32 -lwinmm"
	}
	};

	*nb = sizeof(libraries) / sizeof(libraries[0]);
	return (libraries);
}

const t_lib	*get_lib(size_t index)
{
	size_t	nb;

	return (&get_libraries(&nb)[index]);
}

size_t	get_lib_count(void)
{
	size_t	nb;

	get_libraries(&nb);
	return (nb);
}
