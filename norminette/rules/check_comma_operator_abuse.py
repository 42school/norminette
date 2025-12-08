from norminette.rules import Rule, Check


class CheckCommaOperatorAbuse(Rule, Check):
	depends_on = (
		"IsExpressionStatement",
		"IsDeclaration",
	)

	def count_function_calls_in_parens(self, context, start_pos):
		"""
		Count function calls separated by commas within parentheses.
		Returns the count of function calls found.
		"""
		if not context.check_token(start_pos, "LPARENTHESIS"):
			return 0

		i = start_pos + 1
		func_call_count = 0
		paren_depth = 1

		while i < len(context.tokens) and paren_depth > 0:
			token = context.peek_token(i)
			if token is None:
				break

			# Track nested parentheses
			if context.check_token(i, "LPARENTHESIS"):
				paren_depth += 1
			elif context.check_token(i, "RPARENTHESIS"):
				paren_depth -= 1
				if paren_depth == 0:
					break

			# Look for function call pattern: IDENTIFIER followed by LPARENTHESIS
			# But only at our current depth level (paren_depth == 1)
			if paren_depth == 1:
				if context.check_token(i, "IDENTIFIER"):
					next_i = context.skip_ws(i + 1)
					if context.check_token(next_i, "LPARENTHESIS"):
						func_call_count += 1

			i += 1

		return func_call_count

	def count_assignments_in_parens(self, context, start_pos):
		"""
		Count assignments separated by commas within parentheses.
		Returns the count of assignments found.
		"""
		if not context.check_token(start_pos, "LPARENTHESIS"):
			return 0

		assign_ops = [
			"ASSIGN", "RIGHT_ASSIGN", "LEFT_ASSIGN", "ADD_ASSIGN",
			"SUB_ASSIGN", "MUL_ASSIGN", "DIV_ASSIGN", "MOD_ASSIGN",
			"AND_ASSIGN", "XOR_ASSIGN", "OR_ASSIGN"
		]

		i = start_pos + 1
		assignment_count = 0
		paren_depth = 1

		while i < len(context.tokens) and paren_depth > 0:
			token = context.peek_token(i)
			if token is None:
				break

			# Track nested parentheses
			if context.check_token(i, "LPARENTHESIS"):
				paren_depth += 1
			elif context.check_token(i, "RPARENTHESIS"):
				paren_depth -= 1
				if paren_depth == 0:
					break

			# Look for assignment operators at our depth level
			if paren_depth == 1:
				if context.check_token(i, assign_ops):
					assignment_count += 1

			i += 1

		return assignment_count

	def count_commas_at_depth(self, context, start_pos):
		"""
		Count comma operators at the top level within parentheses.
		This helps identify chained expressions.
		"""
		if not context.check_token(start_pos, "LPARENTHESIS"):
			return 0

		i = start_pos + 1
		comma_count = 0
		paren_depth = 1

		while i < len(context.tokens) and paren_depth > 0:
			token = context.peek_token(i)
			if token is None:
				break

			# Track nested parentheses
			if context.check_token(i, "LPARENTHESIS"):
				paren_depth += 1
			elif context.check_token(i, "RPARENTHESIS"):
				paren_depth -= 1
				if paren_depth == 0:
					break

			# Count commas at top level only
			if paren_depth == 1 and context.check_token(i, "COMMA"):
				comma_count += 1

			i += 1

		return comma_count

	def run(self, context):
		"""
		Detects abuse of comma operators to chain multiple function calls
		or assignments within a single expression statement.

		Example violations:
		- (free(a), free(b), free(c));
		- (i++, j++, k++);
		- return (func1(), func2(), 0);
		"""
		# Scan through all tokens looking for parentheses
		i = 0
		while i < len(context.tokens):
			token = context.peek_token(i)
			if token is None:
				break

			# Look for opening parenthesis
			if context.check_token(i, "LPARENTHESIS"):
				# Count top-level commas within this parenthesis
				comma_count = self.count_commas_at_depth(context, i)

				# If there are commas, check for function calls or assignments
				if comma_count >= 1:
					func_call_count = self.count_function_calls_in_parens(context, i)
					assignment_count = self.count_assignments_in_parens(context, i)

					# If we have multiple function calls or assignments chained with commas
					if func_call_count >= 2 or assignment_count >= 2:
						context.new_error("COMMA_OP_ABUSE", context.peek_token(i))
						return False, 0

			i += 1

		return False, 0
