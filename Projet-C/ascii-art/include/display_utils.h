/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   display_utils.h                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2025/06/25 11:55:46 by cseren            #+#    #+#             */
/*   Updated: 2026/07/10 19:07:14 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef DISPLAY_UTILS_H
# define DISPLAY_UTILS_H
# include <stdio.h>
# include <stdlib.h>
# include <string.h>
# include <dirent.h>
# include <stddef.h>
# define FONT_FOLDER "text"

// display_utils-1.c
void	afficher_ligne(FILE *fp, FILE *out);
void	afficher_police(const char *font, const char *texte, FILE *out,
			int entete);
void	nettoyer_chaine(char *token);
void	afficher_texte_avec_sauts(const char *font, const char *texte,
			FILE *out, int entete);
int		afficher_toutes_polices(const char *texte);

// display_utils-2.c
void	build_text(int argc, char *argv[], char *texte);
int		validate_args(int argc, char *argv[], int *save);
int		open_output_file(int save, FILE **out);

#endif
