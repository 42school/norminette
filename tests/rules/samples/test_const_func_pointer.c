int	with_pointer_return(void)
{
	void	*(*const f)(size_t) = malloc;

	return (f != NULL);
}

int	with_plain_return(void)
{
	void	(*const g)(int) = NULL;

	return (g != NULL);
}
