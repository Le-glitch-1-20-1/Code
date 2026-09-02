/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   input.c                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/09/02 17:58:58 by le-glitch         #+#    #+#             */
/*   Updated: 2026/09/02 20:30:18 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "makefile_generator.h"

int	read_path(char *path, size_t size)
{
	char	fmt[16];

	printf("Enter the project directory path: ");
	snprintf(fmt, sizeof(fmt), "%%%zus", size - 1);
	if (scanf(fmt, path) != 1)
	{
		fprintf(stderr, "Input error.\n");
		return (0);
	}
	return (1);
}

int	read_windows_answer(void)
{
	char	rep;

	rep = 'n';
	printf("Do you want the Makefile to offer Windows compilation?");
	printf(" [y/N] ");
	if (scanf(" %c", &rep) != 1)
	{
		fprintf(stderr, "Input error.\n");
		return (-1);
	}
	return (rep == 'y' || rep == 'Y');
}
