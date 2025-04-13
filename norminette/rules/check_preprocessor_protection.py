import itertools

from norminette.rules import Rule, Check


class CheckPreprocessorProtection(Rule, Check):
    depends_on = (
        "IsPreprocessorStatement",
    )

    def run(self, context):
        """
        Header protection must be as follows:
        ```c
        #ifndef __FILENAME_H__
        # define __FILENAME_H__
        #endif
        OR
        #!defined __FILENAME_H__
        # define __FILENAME_H__
        #endif
        ```
        Any header instruction must be within the header protection
        """
        if context.file.type != ".h":
            return False, 0
        using_defined = False
        i = context.skip_ws(0)
        hash = context.peek_token(i)
        i += 1  # Skip the HASH
        i = context.skip_ws(i)
        if (context.check_token(i, "IF")):
            using_defined = True
            i = context.skip_ws(i + 1)
        if not (not using_defined and context.check_token(i, "IDENTIFIER")
                or using_defined and context.check_token(i, "NOT")):
            return False, 0
        # TODO: Add to check if macro definition is bellow #ifndef
        t = context.peek_token(i)
        if not t or (
                not using_defined
                and (
                    t.type != "IDENTIFIER"
                    or t.value.upper() not in ("IFNDEF", "ENDIF"))
                ):
            return False, 0
        elif using_defined:
            if t.type != "NOT":
                return False, 0
            i = context.skip_ws(i + 1)
            t = context.peek_token(i)
            if not t or t.type != "IDENTIFIER" or t.value != "defined":
                return False, 0
        i += 1
        guard = context.file.basename.upper().replace(".", "_")
        if t.value.upper() == "ENDIF":
            if context.preproc.indent == 0 and not context.protected:
                i = context.skip_ws(i, nl=True, comment=True)
                if context.peek_token(i) is not None:
                    context.new_error("HEADER_PROT_ALL_AF", context.peek_token(i))
                if not context.preproc.has_macro_defined(guard):
                    context.new_error("HEADER_PROT_NODEF", hash)
                context.protected = True
            return False, 0
        if context.preproc.indent != 1:
            return False, 0
        i = context.skip_ws(i)
        macro = context.peek_token(i).value
        if macro != guard and not context.protected:
            if macro.upper() == guard:
                context.new_error("HEADER_PROT_UPPER", context.peek_token(i))
            else:
                context.new_error("HEADER_PROT_NAME", context.peek_token(i))

        if context.protected:
            context.new_error("HEADER_PROT_MULT", hash)
            return False, 0

        headers = (
            "IsComment",
            "IsEmptyLine",
        )
        history = context.history[:-1]  # Remove the current `IsPreprocessorStatement`
        history = itertools.filterfalse(lambda item: item in headers, history)
        if next(history, None):
            # We can't say what line contains the instruction outside
            # header protection due to limited history information.
            context.new_error("HEADER_PROT_ALL", hash)

        return False, 0
