/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_browser-1.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:04:57 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/27 08:31:50 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

void	browser_scan_dir(const char *dirpath, char names[MAX_RLE][128],
			int *count)
{
	DIR				*dir;
	struct dirent	*e;
	int				l;

	dir = opendir(dirpath);
	if (!dir)
		return ;
	e = readdir(dir);
	while (e && *count < MAX_RLE)
	{
		l = (int)strlen(e->d_name);
		if (l > 4 && strcmp(e->d_name + l - 4, ".rle") == 0)
			snprintf(names[(*count)++], 128, "%s/%s", dirpath, e->d_name);
		e = readdir(dir);
	}
	closedir(dir);
}

void	browser_load_files(char names[MAX_RLE][128], int *count)
{
	const char	*dirs[2];
	int			d;

	dirs[0] = "assets/patterns";
	dirs[1] = "saves";
	*count = 0;
	d = 0;
	while (d < 2)
	{
		browser_scan_dir(dirs[d], names, count);
		d++;
	}
}

static void	str_tolower(const char *src, char *dst, int maxlen)
{
	int	i;

	i = 0;
	while (src[i] && i < maxlen - 1)
	{
		dst[i] = tolower((unsigned char)src[i]);
		i++;
	}
	dst[i] = 0;
}

static int	filter_match(const char *name, const char *search)
{
	char	dlow[128];
	char	slow[64];
	char	*slash;

	if (!search[0])
		return (1);
	slash = strrchr(name, '/');
	if (slash)
		name = slash + 1;
	str_tolower(name, dlow, 128);
	str_tolower(search, slow, 64);
	return (strstr(dlow, slow) != NULL);
}

int	browser_filter(char names[MAX_RLE][128], int count, int *filtered,
		const char *search)
{
	int	fcount;
	int	i;

	fcount = 0;
	i = 0;
	while (i < count)
	{
		if (filter_match(names[i], search))
			filtered[fcount++] = i;
		i++;
	}
	return (fcount);
}
