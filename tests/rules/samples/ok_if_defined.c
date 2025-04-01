#if defined FOO
# undef FOO
#elif defined (BAR)
# undef BAR
#elif defined(FOOBAR)
# undef FOOBAR
#endif /* if defined FOO */

#define A defined B

void	defined(void);
