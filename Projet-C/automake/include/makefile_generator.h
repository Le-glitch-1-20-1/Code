/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   makefile_generator.h                              :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 17:58:58 by le-glitch         #+#    #+#             */
/*   Updated: 2026/09/02 20:01:59 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef MAKEFILE_GENERATOR_H
# define MAKEFILE_GENERATOR_H

# include <stdio.h>
# include <stdlib.h>
# include <dirent.h>
# include <string.h>
# include <sys/stat.h>
# include <ctype.h>

# define ALIGN_WIDTH 14
# define PATH_SIZE 1024
# define FLAGS_SIZE 1024
# define MAX_LIBRARIES 16

typedef struct s_lib
{
	const char	*name;
	const char	*header;
	const char	*ldflags_linux;
	const char	*includes_windows;
	const char	*libpath_windows;
	const char	*ldflags_windows;
}	t_lib;

typedef struct s_makefile_context
{
	char	name[256];
	int		has_src;
	int		has_include;
	int		has_ldflags;
	int		want_windows;
	char	ldflags[FLAGS_SIZE];
	char	win_includes[FLAGS_SIZE];
	char	win_libpath[FLAGS_SIZE];
	char	win_ldflags[FLAGS_SIZE];
}	t_makefile_context;

/* libs.c */
const t_lib	*get_lib(size_t index);
size_t		get_lib_count(void);

/* parse_include.c */
int			line_contains_include(const char *line, const char *header);
int			is_target_file(const char *name);

/* file_scan.c */
int			file_contains_include(const char *path, const char *header);
int			directory_contains_include(const char *path, const char *header);

/* directory_scan.c */
int			check_root_c_files(const char *path, const char *header,
				int *found_c);
int			project_uses(const char *path, const char *header);

/* directory_name.c */
int			is_a_directory(const char *path);
void		get_directory_name(const char *path, char *dest, size_t size);

/* makefile_vars.c */
void		write_variable(FILE *f, const char *name, const char *value);
void		compute_ldflags(char *ldflags, const int *results);
void		compute_windows_flags(char *includes, char *libpath, char *ldflags,
				const int *results);

/* makefile_rules-1.c */
void		write_compilation_variables(FILE *f, t_makefile_context *ctx);
void		write_file_variables(FILE *f, t_makefile_context *ctx);
void		write_all_rule(FILE *f, t_makefile_context *ctx);

/* makefile_rules-2.c */
void		write_compilation_rules(FILE *f, t_makefile_context *ctx);
void		write_windows_rule(FILE *f, t_makefile_context *ctx);
void		write_cleanup_rules(FILE *f, t_makefile_context *ctx);

/* makefile_generator.c */
void		prepare_context(const char *project_path, const int *results,
				int want_windows, t_makefile_context *ctx);
void		generate_makefile(const char *project_path, const int *results,
				int want_windows);

/* input.c */
int			read_path(char *path, size_t size);
int			read_windows_answer(void);

#endif
