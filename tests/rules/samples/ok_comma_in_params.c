/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ok_comma_in_params.c                               :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: norminette <norminette@student.42.fr>      +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2025/12/08 00:00:00 by norminette        #+#    #+#             */
/*   Updated: 2025/12/08 00:00:00 by norminette       ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include <stdio.h>

void	test_proper_comma_use(void)
{
	int	a;
	int	b;
	int	c;

	printf("%d %d %d", a, b, c);
	a = 1;
	b = 2;
	c = 3;
}

int	test_proper_return(void)
{
	int	result;

	result = calculate(1, 2, 3);
	return (result);
}
