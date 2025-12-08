/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ko_comma_operator_abuse.c                          :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: norminette <norminette@student.42.fr>      +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2025/12/08 00:00:00 by norminette        #+#    #+#             */
/*   Updated: 2025/12/08 00:00:00 by norminette       ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include <stdlib.h>

void	test_comma_abuse(void)
{
	char	*a;
	char	*b;
	char	*c;

	(free(a), free(b), free(c));
}

int	test_return_abuse(void)
{
	char	*a;
	char	*b;

	return (free(a), free(b), 0);
}
