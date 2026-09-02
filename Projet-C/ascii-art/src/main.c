/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.c                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2025/06/25 12:24:06 by cseren            #+#    #+#             */
/*   Updated: 2026/09/02 17:41:42 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "display_utils.h"

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
		printf("Sauvegarde dans font.txt terminée.\n");
	}
	return (0);
}
