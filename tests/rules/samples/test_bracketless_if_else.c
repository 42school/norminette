int	main(int a, int b)
{
	while (a)
		if (b)
			break ;
		else if (a)
			return (0);
		else
			return (1);
	while (a)
		while (b)
			if (a)
				break ;
			else
				return (1);
	if (a)
		if (b)
			return (0);
		else
			return (1);
	return (a + b);
}
