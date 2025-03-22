#if defined FOO
# undef FOO
#elif defined (BAR)
# undef BAR
#elif defined(FOOBAR)
# undef FOOBAR
#endif /* if defined FOO */

void	defined(void);
