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

int	browser_filter(char names[MAX_RLE][128], int count, int *filtered,
		const char *search)
{
	int			fcount;
	int			i;
	int			j;
	int			dl;
	int			sl;
	char		dlow[128];
	char		slow[64];
	const char	*slash;
	const char	*dname;

	fcount = 0;
	i = 0;
	while (i < count)
	{
		if (!search[0])
		{
			filtered[fcount++] = i;
		}
		else
		{
			slash = strrchr(names[i], '/');
			if (slash)
				dname = slash + 1;
			else
				dname = names[i];
			dl = (int)strlen(dname);
			sl = (int)strlen(search);
			j = 0;
			while (j < dl && j < 127)
			{
				dlow[j] = tolower((unsigned char)dname[j]);
				j++;
			}
			if (dl < 127)
				dlow[dl] = 0;
			else
				dlow[127] = 0;
			j = 0;
			while (j < sl && j < 63)
			{
				slow[j] = tolower((unsigned char)search[j]);
				j++;
			}
			if (sl < 63)
				slow[sl] = 0;
			else
				slow[63] = 0;
			if (strstr(dlow, slow))
				filtered[fcount++] = i;
		}
		i++;
	}
	return (fcount);
}
