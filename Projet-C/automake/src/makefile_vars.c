/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   makefile_vars.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 17:58:58 by le-glitch         #+#    #+#             */
/*   Updated: 2026/09/02 20:35:22 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "makefile_generator.h"

void	write_variable(FILE *f, const char *name, const char *value)
{
	fprintf(f, "%-*s:= %s\n", ALIGN_WIDTH, name, value);
}

static void	add_flag(char *dest, const char *flag)
{
	if (flag[0] == '\0')
		return ;
	if (dest[0] != '\0')
		strcat(dest, " ");
	strcat(dest, flag);
}

void	compute_ldflags(char *ldflags, const int *results)
{
	size_t	i;

	i = 0;
	while (i < get_lib_count())
	{
		if (results[i])
			add_flag(ldflags, get_lib(i)->ldflags_linux);
		i++;
	}
}

void	compute_windows_flags(char *includes, char *libpath, char *ldflags,
		const int *results)
{
	size_t		i;
	const t_lib	*lib;

	i = 0;
	while (i < get_lib_count())
	{
		if (results[i])
		{
			lib = get_lib(i);
			add_flag(includes, lib->includes_windows);
			add_flag(libpath, lib->libpath_windows);
			add_flag(ldflags, lib->ldflags_windows);
		}
		i++;
	}
}
