/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.c                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 17:58:58 by le-glitch         #+#    #+#             */
/*   Updated: 2026/09/02 20:35:14 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "makefile_generator.h"

static void	display_result(const t_lib *lib, int found)
{
	if (found)
		printf("%s: found\n", lib->name);
	else
		printf("%s: not found\n", lib->name);
}

static void	detect_libraries(const char *path, int *results)
{
	size_t		i;
	const t_lib	*lib;

	i = 0;
	while (i < get_lib_count())
	{
		lib = get_lib(i);
		results[i] = project_uses(path, lib->header);
		display_result(lib, results[i]);
		i++;
	}
}

int	main(void)
{
	char	path[PATH_SIZE];
	int		results[MAX_LIBRARIES];
	int		want_windows;

	if (!read_path(path, sizeof(path)))
		return (EXIT_FAILURE);
	detect_libraries(path, results);
	want_windows = read_windows_answer();
	if (want_windows == -1)
		return (EXIT_FAILURE);
	generate_makefile(path, results, want_windows);
	return (0);
}
