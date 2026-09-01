int	main(char *grid, int size, int *p)
{
	int	i;

	i = 0;
	grid[size + i++ * (size + 1)] = 'x';
	grid[i++ * 2] = 'x';
	grid[i-- * 2] = 'x';
	i = *p;
	i = ++*p;
	i = *p++;
	return (i);
}
