int	main(void)
{
	get_data(NULL)->files_fds[INFILE] = open(argv[1], O_RDONLY);
	return (0);
}
