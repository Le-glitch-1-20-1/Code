/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.c                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2025/06/25 12:24:06 by cseren            #+#    #+#             */
/*   Updated: 2026/05/03 16:18:23 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include <stdio.h>
#include <string.h>
#include <stddef.h>
#include "display_utils.h"

static int	open_output_file(int save, FILE **out)
{
	if (save)
	{
		*out = fopen("font.txt", "w");
		if (*out == NULL)
		{
			perror("Erreur ouverture font.txt");
			return (1);
		}
	}
	return (0);
}

static void	build_text(int argc, char *argv[], char *texte)
{
	int	i;

	i = 2;
	texte[0] = '\0';
	while (i < argc)
	{
		strcat(texte, argv[i]);
		if (i < argc - 1)
			strcat(texte, " ");
		i++;
	}
}

static int	validate_args(int argc, char *argv[], int *save)
{
	if (argc == 2 && strcmp(argv[1], "font-test-txt") == 0)
		return (afficher_toutes_polices("TXT"));
	if (argc < 3)
	{
		fprintf(stderr, "Usage:\n");
		fprintf(stderr, "  %s font_name texte [o]\n", argv[0]);
		return (-1);
	}
	*save = 0;
	if (argc >= 4 && strcmp(argv[argc - 1], "o") == 0)
	{
		*save = 1;
		return (argc - 1);
	}
	return (argc);
}

int	main(int argc, char *argv[])
{
	FILE	*out;
	char	texte[512];
	char	font_path[512];
	int		save;
	int		new_argc;

	new_argc = validate_args(argc, argv, &save);
	if (new_argc == -1)
		return (1);
	if (new_argc != argc)
		argc = new_argc;
	build_text(argc, argv, texte);
	out = NULL;
	if (open_output_file(save, &out) != 0)
		return (1);
	snprintf(font_path, sizeof(font_path), "%s/%s", FONT_FOLDER, argv[1]);
	afficher_texte_avec_sauts(font_path, texte, out, 0);
	if (out != NULL)
	{
		fclose(out);
		printf("✔ Sauvegarde dans font.txt terminée.\n");
	}
	return (0);
}
