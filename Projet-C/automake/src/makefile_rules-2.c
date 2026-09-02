/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   makefile_rules-2.c                                 :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 17:58:58 by le-glitch         #+#    #+#             */
/*   Updated: 2026/09/02 20:29:05 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "makefile_generator.h"

void	write_compilation_rules(FILE *f, t_makefile_context *ctx)
{
	fprintf(f, "# Creating the Linux executable\n");
	fprintf(f, "$(NAME): $(OBJ)\n");
	if (ctx->has_ldflags)
		fprintf(f, "\t$(CC) $(CFLAGS) $(OBJ) -o $(NAME) $(LDFLAGS)\n\n");
	else
		fprintf(f, "\t$(CC) $(CFLAGS) $(OBJ) -o $(NAME)\n\n");
	fprintf(f, "# Compiling .c files into .o in o/\n");
	if (ctx->has_src)
		fprintf(f, "$(OBJ_DIR)/%%.o: $(SRC_DIR)/%%.c | $(OBJ_DIR)\n");
	else
		fprintf(f, "$(OBJ_DIR)/%%.o: %%.c | $(OBJ_DIR)\n");
	fprintf(f, "\t$(CC) $(CFLAGS) -c $< -o $@\n\n");
	fprintf(f, "# Creating the o/ directory if missing\n");
	fprintf(f, "$(OBJ_DIR):\n");
	fprintf(f, "\tmkdir -p $(OBJ_DIR)\n\n");
}

void	write_windows_rule(FILE *f, t_makefile_context *ctx)
{
	if (!ctx->want_windows)
		return ;
	fprintf(f, "# Windows build (.exe, no console), invoked if requested\n");
	fprintf(f, ".PHONY: windows\n");
	fprintf(f, "windows: $(SRC)\n");
	fprintf(f, "\t$(CC_WIN) $(CFLAGS) $(SRC) -o $(NAME).exe \\\n");
	fprintf(f, "\t\t-mwindows -Wl,--subsystem,windows \\\n");
	fprintf(f, "\t\t$(WIN_INCLUDES) $(WIN_LIBPATH) $(WIN_LDFLAGS)\n");
	fprintf(f, "\t@echo \">> Windows build finished -> $(NAME).exe\"\n\n");
}

void	write_cleanup_rules(FILE *f, t_makefile_context *ctx)
{
	fprintf(f, "# Cleanup\n");
	fprintf(f, "clean:\n");
	fprintf(f, "\trm -rf $(OBJ_DIR)\n\n");
	fprintf(f, "fclean: clean\n");
	if (ctx->want_windows)
		fprintf(f, "\trm -f $(NAME) $(NAME).exe\n\n");
	else
		fprintf(f, "\trm -f $(NAME)\n\n");
	fprintf(f, "re: fclean all\n\n");
	fprintf(f, ".PHONY: all clean fclean re\n");
}
