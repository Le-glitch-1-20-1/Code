/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_savezone-3.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/21 23:06:43 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 22:48:16 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"

int	is_valid_name_char(int k)
{
	if ((k >= 'a' && k <= 'z') || (k >= 'A' && k <= 'Z'))
		return (1);
	if ((k >= '0' && k <= '9') || k == '_' || k == '-')
		return (1);
	return (0);
}

void	sz_name_edit(t_save_zone_state *sz)
{
	int	k;
	int	len;

	k = GetCharPressed();
	while (k > 0)
	{
		len = (int)strlen(sz->name_buf);
		if (is_valid_name_char(k) && len < 60)
		{
			sz->name_buf[len] = (char)k;
			sz->name_buf[len + 1] = 0;
		}
		k = GetCharPressed();
	}
	if (IsKeyPressed(KEY_BACKSPACE))
	{
		len = (int)strlen(sz->name_buf);
		if (len > 0)
			sz->name_buf[len - 1] = 0;
	}
}
