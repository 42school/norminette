int	main(int v1, int v2)
{
	if (get_res((t_stct){v1, v2}, 1) == 1)
		return (1);
	if (get_res((t_stct){.i = v1, .j = v2}, 1) == 1)
		return (2);
	if ((v1 = v2) == 1)
		return (3);
	return (0);
}
