/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   display_utils-2.c                                  :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/03 16:17:09 by le-glitch         #+#    #+#             */
/*   Updated: 2026/09/02 21:32:34 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "display_utils.h"

int	open_output_file(int save, FILE **out)
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

void	build_text(int argc, char *argv[], char *texte)
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

int	validate_args(int argc, char *argv[], int *save)
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
