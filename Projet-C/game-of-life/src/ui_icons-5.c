/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ui_icons-5.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: le-glitch <le-glitch@student.42.fr>        +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 07:29:12 by le-glitch         #+#    #+#             */
/*   Updated: 2026/06/23 07:28:41 by le-glitch        ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ui.h"
#include "ui_shared.h"
#include "ui_icons.h"

#include "main.h"

void	icon_paste(float cx, float cy, float r, Color c)
{
	Vector2	arr[3];

	DrawRectangleLinesEx((Rectangle){cx - r * 0.65f, cy - r * 0.7f,
		(int)(r * 1.3f), (int)(r * 1.5f)}, 1.5f, c);
	DrawRectangle((int)(cx - r * 0.35f), (int)(cy - r * 0.9f),
		(int)(r * 0.7f), (int)(r * 0.35f), c);
	DrawLineEx((Vector2){cx, cy - r * 0.15f},
		(Vector2){cx, cy + r * 0.55f}, 1.8f, c);
	arr[0] = (Vector2){cx - r * 0.3f, cy + r * 0.3f};
	arr[1] = (Vector2){cx + r * 0.3f, cy + r * 0.3f};
	arr[2] = (Vector2){cx, cy + r * 0.65f};
	DrawTriangle(arr[0], arr[1], arr[2], c);
}
