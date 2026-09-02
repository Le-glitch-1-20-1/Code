/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   makefile_rules-1.c                                 :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 17:58:58 by le-glitch         #+#    #+#             */
/*   Updated: 2026/09/02 20:41:05 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "makefile_generator.h"

void	write_compilation_variables(FILE *f, t_makefile_context *ctx)
{
	char	cflags_val[256];
	char	extra_include[32];

	write_variable(f, "CC", "gcc");
	if (ctx->want_windows)
		write_variable(f, "CC_WIN", "x86_64-w64-mingw32-gcc");
	extra_include[0] = '\0';
	if (ctx->has_include)
		snprintf(extra_include, sizeof(extra_include), " -I include/");
	snprintf(cflags_val, sizeof(cflags_val), "-Wall -Wextra -Werror -Wunused%s",
		extra_include);
	write_variable(f, "CFLAGS", cflags_val);
	if (ctx->has_ldflags)
		write_variable(f, "LDFLAGS", ctx->ldflags);
	if (ctx->want_windows)
	{
		write_variable(f, "WIN_INCLUDES", ctx->win_includes);
		write_variable(f, "WIN_LIBPATH", ctx->win_libpath);
		write_variable(f, "WIN_LDFLAGS", ctx->win_ldflags);
	}
	fprintf(f, "\n");
}

void	write_file_variables(FILE *f, t_makefile_context *ctx)
{
	if (ctx->has_src)
		write_variable(f, "SRC_DIR", "src");
	write_variable(f, "OBJ_DIR", "o");
	write_variable(f, "NAME", ctx->name);
	fprintf(f, "\n");
	fprintf(f, "# List of .c files\n");
	if (ctx->has_src)
		write_variable(f, "SRC", "$(wildcard $(SRC_DIR)/*.c)");
	else
		write_variable(f, "SRC", "$(wildcard *.c)");
	fprintf(f, "\n");
	fprintf(f, "# Transform into .o files in o/\n");
	if (ctx->has_src)
		write_variable(f, "OBJ",
			"$(patsubst $(SRC_DIR)/%.c, $(OBJ_DIR)/%.o, $(SRC))");
	else
		write_variable(f, "OBJ", "$(patsubst %.c, $(OBJ_DIR)/%.o, $(SRC))");
	fprintf(f, "\n");
}

void	write_all_rule(FILE *f, t_makefile_context *ctx)
{
	if (!ctx->want_windows)
	{
		fprintf(f, "# Default rule\n");
		fprintf(f, "all: $(NAME)\n\n");
		return ;
	}
	fprintf(f, "# Default rule:\n");
	fprintf(f, "#  - always builds Linux first\n");
	fprintf(f, "#  - on failure -> make stops, Windows is NOT offered\n");
	fprintf(f, "#  - on success -> asks whether to also build for Windows\n");
	fprintf(f, "all: $(NAME)\n");
	fprintf(f, "\t@read -p \">> Also build for Windows? [y/N] \"");
	fprintf(f, " rep; \\\n");
	fprintf(f,
		"\tif [ \"$$rep\" = \"y\" ] || [ \"$$rep\" = \"Y\" ]; then \\\n");
	fprintf(f, "\t\t$(MAKE) --no-print-directory windows; \\\n");
	fprintf(f, "\telse \\\n");
	fprintf(f, "\t\techo \">> Windows build cancelled.\"; \\\n");
	fprintf(f, "\tfi\n\n");
}
