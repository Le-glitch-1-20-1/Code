/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   display_utils.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/03 16:17:09 by le-glitch         #+#    #+#             */
/*   Updated: 2026/05/03 16:17:10 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include "display_utils.h"
#define FONT_FOLDER "text"

void	afficher_ligne(FILE *fp, FILE *out)
{
	char	line[2048];

	while (fgets(line, sizeof(line), fp))
	{
		printf("%s", line);
		if (out != NULL)
			fprintf(out, "%s", line);
	}
}

void	afficher_police(
			const char *font,
			const char *texte,
			FILE *out,
			int entete)
{
	FILE	*fp;
	char	cmd[2048];

	snprintf(cmd, sizeof(cmd), "figlet -f \"%s\" -w 10000 \"%s\"", font, texte);
	fp = popen(cmd, "r");
	if (fp == NULL)
	{
		fprintf(stderr, "Erreur figlet avec %s\n", font);
		return ;
	}
	if (entete == 1)
	{
		printf("=== Police : %s ===\n", font);
		if (out != NULL)
			fprintf(out, "=== Police : %s ===\n", font);
	}
	afficher_ligne(fp, out);
	printf("\n");
	if (out != NULL)
		fprintf(out, "\n");
	pclose(fp);
}

static void	nettoyer_chaine(char *token)
{
	char	*end;

	while (*token == ' ')
		token++;
	end = token + strlen(token) - 1;
	while (end > token && *end == ' ')
	{
		*end = '\0';
		end--;
	}
}

void	afficher_texte_avec_sauts(
			const char *font,
			const char *texte,
			FILE *out,
			int entete)
{
	char	temp[1024];
	char	*token;

	strncpy(temp, texte, sizeof(temp) - 1);
	temp[sizeof(temp) - 1] = '\0';
	token = strtok(temp, "|");
	while (token != NULL)
	{
		nettoyer_chaine(token);
		if (strlen(token) > 0)
			afficher_police(font, token, out, entete);
		token = strtok(NULL, "|");
	}
}

int	afficher_toutes_polices(const char *texte)
{
	DIR				*d;
	struct dirent	*entry;
	char			path[512];

	d = opendir(FONT_FOLDER);
	if (d == NULL)
	{
		perror("Erreur ouverture dossier fonts");
		return (1);
	}
	entry = readdir(d);
	while (entry != NULL)
	{
		if (strstr(entry->d_name, ".flf") != NULL)
		{
			snprintf(path, sizeof(path), "%s/%s", FONT_FOLDER, entry->d_name);
			afficher_police(path, texte, NULL, 1);
		}
		entry = readdir(d);
	}
	closedir(d);
	return (0);
}
