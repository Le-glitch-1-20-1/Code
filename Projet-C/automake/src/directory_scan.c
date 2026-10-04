/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   directory_scan.c                                   :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 17:58:58 by le-glitch         #+#    #+#             */
/*   Updated: 2026/09/02 21:34:57 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "makefile_generator.h"

int	process_c_file(const char *full_path, const char *header,
		int *found_c)
{
	*found_c = 1;
	return (file_contains_include(full_path, header));
}

int	examine_element(const char *path, const char *name,
		const char *header, int *found_c)
{
	char		full_path[PATH_SIZE];
	struct stat	st;
	size_t		len;

	snprintf(full_path, sizeof(full_path), "%s/%s", path, name);
	if (stat(full_path, &st) != 0 || !S_ISREG(st.st_mode))
		return (0);
	len = strlen(name);
	if (len >= 2 && strcmp(name + len - 2, ".c") == 0)
		return (process_c_file(full_path, header, found_c));
	return (0);
}

int	check_root_c_files(const char *path, const char *header,
		int *found_c)
{
	DIR				*directory;
	struct dirent	*entry;
	int				found;

	*found_c = 0;
	found = 0;
	directory = opendir(path);
	if (directory == NULL)
	{
		perror("Unable to open directory");
		return (0);
	}
	entry = readdir(directory);
	while (entry != NULL)
	{
		if (strcmp(entry->d_name, ".") != 0
			&& strcmp(entry->d_name, "..") != 0
			&& examine_element(path, entry->d_name, header, found_c))
			found = 1;
		entry = readdir(directory);
	}
	closedir(directory);
	return (found);
}

int	search_in_subdirectory(const char *path, const char *name,
		const char *header)
{
	char	subdirectory[PATH_SIZE];

	snprintf(subdirectory, sizeof(subdirectory), "%s/%s", path, name);
	if (is_a_directory(subdirectory))
		return (directory_contains_include(subdirectory, header));
	return (0);
}

int	project_uses(const char *path, const char *header)
{
	int	has_root_c;
	int	found;

	found = check_root_c_files(path, header, &has_root_c);
	if (has_root_c)
		return (found);
	return (search_in_subdirectory(path, "src", header)
		|| search_in_subdirectory(path, "include", header));
}
