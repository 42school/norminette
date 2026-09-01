void	func(void **arr, char *str, int a)
{
	a = (a + 1) * 2;
	str = (((char **)arr)[1] = str);
}
