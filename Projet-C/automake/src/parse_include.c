/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   parse_include.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 17:58:58 by le-glitch         #+#    #+#             */
/*   Updated: 2026/09/02 20:25:01 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "makefile_generator.h"

int	line_contains_include(const char *line, const char *header)
{
	const char	*p;
	char		pattern[128];

	p = line;
	while (isspace((unsigned char)*p))
		p++;
	if (*p != '#')
		return (0);
	p++;
	while (isspace((unsigned char)*p))
		p++;
	if (strncmp(p, "include", 7) != 0)
		return (0);
	p += 7;
	while (isspace((unsigned char)*p))
		p++;
	snprintf(pattern, sizeof(pattern), "\"%s\"", header);
	return (strstr(p, pattern) != NULL);
}

int	is_target_file(const char *name)
{
	size_t	len;

	len = strlen(name);
	if (len < 3)
		return (0);
	return (strcmp(name + len - 2, ".c") == 0
		|| strcmp(name + len - 2, ".h") == 0);
}
