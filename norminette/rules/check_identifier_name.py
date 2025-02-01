import string

from norminette.rules import Rule, Check
from norminette.scope import GlobalScope, UserDefinedType
from norminette.errors import Error


assigns = ["ASSIGN"]


class CheckIdentifierName(Rule, Check):
    def run(self, context):
        """
        Function can only be declared in the global scope
        User defined identifiers can only contain lowercase characters, '_' or digits
        """
        legal_characters = string.ascii_lowercase + string.digits + "_"
        if context.history[-1] == "IsFuncDeclaration":
            sc = context.scope
            if type(sc) is not GlobalScope and type(sc) is not UserDefinedType:
                context.new_error("WRONG_SCOPE_FCT", context.peek_token(0))
            while type(sc) != GlobalScope:
                sc = sc.outer()
            for c in sc.fnames[-1]:
                if c not in legal_characters:
                    token = context.peek_token(context.fname_pos)
                    error = Error.from_name("FORBIDDEN_CHAR_NAME")
                    error.add_highlight(token)
                    context.errors.add(error)
        if len(context.scope.vars_name) > 0:
            for val in context.scope.vars_name[::]:
                for c in val.value:
                    if c not in legal_characters:
                        error = Error.from_name("FORBIDDEN_CHAR_NAME")
                        error.add_highlight(val)
                        context.errors.add(error)
                        break
                context.scope.vars_name.remove(val)
        return False, 0
