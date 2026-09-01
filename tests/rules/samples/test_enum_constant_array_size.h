#define LEN 4

enum	e_actions
{
	action_init,
	action_clear,
	last_action
};

typedef int	(*t_fn)(void);

t_fn	g_from_enum[last_action];
t_fn	g_from_macro[LEN];
t_fn	g_from_literal[4];
