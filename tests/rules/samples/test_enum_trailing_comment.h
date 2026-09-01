#ifndef TEST_ENUM_TRAILING_COMMENT_H
# define TEST_ENUM_TRAILING_COMMENT_H

typedef enum e_type
{
	TEX,
	COLOR,		// with a comma
	OTHER,
	UNKNOWN		/* block, no comma */
}	t_type;

int	ft_a(void);

#endif
