/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   directory_name.c                                   :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 17:58:58 by le-glitch         #+#    #+#             */
/*   Updated: 2026/09/02 20:26:29 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "makefile_generator.h"

int	is_a_directory(const char *path)
{
	struct stat	st;

	if (stat(path, &st) != 0)
		return (0);
	return (S_ISDIR(st.st_mode));
}

static size_t	find_name_start(const char *path, size_t len)
{
	size_t	start;

	start = len;
	while (start > 0 && path[start - 1] != '/')
		start--;
	return (start);
}

void	get_directory_name(const char *path, char *dest, size_t size)
{
	size_t	len;
	size_t	start;
	size_t	n;

	len = strlen(path);
	while (len > 1 && path[len - 1] == '/')
		len--;
	start = find_name_start(path, len);
	n = len - start;
	if (n == 0)
	{
		snprintf(dest, size, "program");
		return ;
	}
	if (n >= size)
		n = size - 1;
	memcpy(dest, path + start, n);
	dest[n] = '\0';
}
