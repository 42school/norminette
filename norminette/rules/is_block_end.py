from norminette.context import ControlStructure
from norminette.scope import UserDefinedEnum
from norminette.scope import UserDefinedType
from norminette.scope import VariableAssignation
from norminette.rules import Rule, Primary


class IsBlockEnd(Rule, Primary, priority=54):
    def check_udef_typedef(self, context, pos):
        i = context.skip_ws(pos)
        if context.check_token(i, "IDENTIFIER") is False:
            return False, 0
        while context.check_token(i, ["IDENTIFIER", "SPACE", "TAB"]):
            i += 1
        i = context.skip_ws(i)
        if context.check_token(i, "SEMI_COLON") is False:
            return False, 0
        i += 1
        return True, i

    def run(self, context):
        """
        Catches RBRACE tokens.
        Handles scope related stuff: Exiting a scope is done here and in registry.py
        Scope is calculated AFTER the rules have run for this primary rule
        """
        i = context.skip_ws(0)
        if context.check_token(i, "RBRACE") is False:
            return False, 0
        if type(context.scope) is not ControlStructure:
            context.sub = context.scope.outer()
        else:
            context.scope.multiline = False
        i += 1
        if type(context.scope) in (UserDefinedType, UserDefinedEnum):
            i = context.skip_ws(i)
            if context.check_token(i, "TYPEDEF") is True:
                i += 1
                ret, i = self.check_udef_typedef(context, i)
                i = context.eol(i)
                return ret, i
            elif context.check_token(i, "SEMI_COLON") is True:
                i += 1
                i = context.eol(i)
                return True, i

            ret, i = self.check_udef_typedef(context, i)
            i = context.eol(i)
            return ret, i

        if type(context.scope) is VariableAssignation:
            i = context.skip_ws(i)
            if context.check_token(i, "SEMI_COLON"):
                # Fatal err?
                return False, 0
            i += 1
            i = context.eol(i)
            return True, i
            pass
        if type(context.scope) is ControlStructure:
            pass
        i = context.eol(i)
        return True, i
