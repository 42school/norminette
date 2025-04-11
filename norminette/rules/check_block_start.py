from norminette.rules import Rule, Check
from norminette.scope import GlobalScope, ControlStructure


class CheckBlockStart(Rule, Check):
    depends_on = (
        "IsBlockStart",
    )

    def run(self, context):
        """
        Braces signal that the control structure, function, or user defined type can contain
        multiple lines.
        A control structure that has no braces can only contain one instruction line, but can
        contain multiple control structures
        """
        outer = context.scope.get_outer()
        if len(context.history) > 2:
            i = 0
            for item in context.history[::]:
                if item != "IsEmptyLine":
                    if i == 2:
                        hist_1 = item
                    elif i == 3:
                        hist_2 = item
                    i += 1
            if (
                type(context.scope) is GlobalScope
                and context.scope.tmp_scope is not None
                and hist_1 == "IsFuncDeclaration"
                and hist_2 == "IsPreprocessorStatement"
            ):
                context.scope.functions -= 1
                context.scope = context.tmp_scope
                context.scope.multiline = True
                context.tmp_scope = None
        if (
            type(context.scope) is ControlStructure
            and outer is not None
            and type(outer) is ControlStructure
        ):
            if outer.multiline is False:
                context.new_error("MULT_IN_SINGLE_INSTR", context.peek_token(0))
        return False, 0
