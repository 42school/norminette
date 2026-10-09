typedef void	t_thing;

t_thing	*new_thing(
			void);
void	free_thing(
			t_thing *self,
			void (*fn)(void *value));
t_thing	*empty_thing(
			);
