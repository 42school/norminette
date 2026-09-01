int	main(int a)
{
	if (pthread_create(&philos[a].thread, NULL, \
			check_status, &philos[a]))
		return (-1);
	return (foo(a), \
			bar(a));
}
