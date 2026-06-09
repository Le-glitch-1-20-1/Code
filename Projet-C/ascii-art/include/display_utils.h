/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   display_utils.h                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cseren <cseren@student.42.fr>              +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2025/06/25 11:55:46 by cseren            #+#    #+#             */
/*   Updated: 2025/06/26 10:02:41 by cseren           ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef DISPLAY_UTILS_H
# define DISPLAY_UTILS_H
# include <stdio.h>
# define FONT_FOLDER "text"

int		run_program(int argc, char *argv[]);
void	afficher_ligne(FILE *fp, FILE *out);
void	afficher_police(
			const char *font,
			const char *texte,
			FILE *out,
			int entete);
void	afficher_texte_avec_sauts(
			const char *font,
			const char *texte,
			FILE *out,
			int entete);
int		afficher_toutes_polices(const char *texte);

#endif
