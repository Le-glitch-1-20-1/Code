/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   file_scan.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 17:58:58 by le-glitch         #+#    #+#             */
/*   Updated: 2026/09/02 20:37:57 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "makefile_generator.h"

int	file_contains_include(const char *path, const char *header)
{
	char	line[512];
	int		found;
	FILE	*f;

	found = 0;
	f = fopen(path, "r");
	if (!f)
		return (0);
	while (fgets(line, sizeof(line), f))
	{
		if (line_contains_include(line, header))
		{
			found = 1;
			break ;
		}
	}
	fclose(f);
	return (found);
}

static int	process_entry(const char *full_path, struct stat *st,
		const char *header)
{
	if (S_ISDIR(st->st_mode))
		return (directory_contains_include(full_path, header));
	if (S_ISREG(st->st_mode) && is_target_file(full_path))
		return (file_contains_include(full_path, header));
	return (0);
}

static int	valid_entry(const char *path, struct dirent *entry,
		char *full_path)
{
	if (strcmp(entry->d_name, ".") == 0
		|| strcmp(entry->d_name, "..") == 0)
		return (0);
	snprintf(full_path, PATH_SIZE, "%s/%s", path, entry->d_name);
	return (1);
}

int	directory_contains_include(const char *path, const char *header)
{
	struct dirent	*entry;
	int				found;
	DIR				*dir;
	char			full_path[PATH_SIZE];
	struct stat		st;

	found = 0;
	dir = opendir(path);
	if (!dir)
		return (0);
	entry = readdir(dir);
	while (entry != NULL)
	{
		if (valid_entry(path, entry, full_path)
			&& stat(full_path, &st) == 0
			&& process_entry(full_path, &st, header))
			found = 1;
		entry = readdir(dir);
	}
	closedir(dir);
	return (found);
}
