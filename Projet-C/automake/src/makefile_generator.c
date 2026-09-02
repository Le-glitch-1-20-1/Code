/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   makefile_generator.c                               :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 17:58:58 by le-glitch         #+#    #+#             */
/*   Updated: 2026/09/02 20:29:51 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "makefile_generator.h"

void	prepare_context(const char *project_path, const int *results,
		int want_windows, t_makefile_context *ctx)
{
	char	src_dir[PATH_SIZE];
	char	include_dir[PATH_SIZE];

	get_directory_name(project_path, ctx->name, sizeof(ctx->name));
	snprintf(src_dir, sizeof(src_dir), "%s/src", project_path);
	ctx->has_src = is_a_directory(src_dir);
	snprintf(include_dir, sizeof(include_dir), "%s/include", project_path);
	ctx->has_include = is_a_directory(include_dir);
	ctx->ldflags[0] = '\0';
	compute_ldflags(ctx->ldflags, results);
	ctx->has_ldflags = (ctx->ldflags[0] != '\0');
	ctx->want_windows = want_windows;
	ctx->win_includes[0] = '\0';
	ctx->win_libpath[0] = '\0';
	ctx->win_ldflags[0] = '\0';
	if (want_windows)
		compute_windows_flags(ctx->win_includes, ctx->win_libpath,
			ctx->win_ldflags, results);
}

void	generate_makefile(const char *project_path, const int *results,
		int want_windows)
{
	t_makefile_context	ctx;
	char				makefile_path[PATH_SIZE + 32];
	FILE				*f;

	prepare_context(project_path, results, want_windows, &ctx);
	snprintf(makefile_path, sizeof(makefile_path), "%s/Makefile",
		project_path);
	f = fopen(makefile_path, "w");
	if (!f)
	{
		perror("Error while creating the Makefile");
		return ;
	}
	write_compilation_variables(f, &ctx);
	write_file_variables(f, &ctx);
	write_all_rule(f, &ctx);
	write_compilation_rules(f, &ctx);
	write_windows_rule(f, &ctx);
	write_cleanup_rules(f, &ctx);
	fclose(f);
	printf("Makefile successfully generated in %s (NAME = %s).\n",
		makefile_path, ctx.name);
}
