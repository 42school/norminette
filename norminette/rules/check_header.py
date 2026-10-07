from norminette.rules import Rule, Check
import re


class CheckHeader(Rule, Check):
    def parse_header(self, context):
        if context.check_token(0, "MULT_COMMENT") is False:
            context.new_error("INVALID_HEADER", context.peek_token(0))
            context.header_parsed = True
            return
        context.header += context.peek_token(0).value + "\n"

    def check_header(self, context):
        # val = r"\/\* \*{74} \*\/\n\/\*.*\*\/\n\/\*.*\*\/\n\/\*.{3}([^ ]*).*\*\/\n\/\*.*\*\/\n\/\*   By: ([^ ]*).*\*\/\n\/\*.*\*\/\n\/\*   Created: ([^ ]* [^ ]*) by ([^ ]*).*\*\/\n\/\*   Updated: ([^ ]* [^ ]*) by ([^ ]*).*\*\/\n\/\*.*\*\/\n\/\* \*{74} \*\/\n" # noqa: E501
        # Every field has to carry a value, an empty one is not a header
        val_no_check_nl = r"\/\* \*{74} \*\/.\/\*.*\*\/.\/\*.*\*\/.\/\*.{3}([^ ]+).*\*\/.\/\*.*\*\/.\/\*   By: ([^ ]+).*\*\/.\/\*.*\*\/.\/\*   Created: ([^ ]+ [^ ]+) by ([^ ]+).*\*\/.\/\*   Updated: ([^ ]+ [^ ]+) by ([^ ]+).*\*\/.\/\*.*\*\/.\/\* \*{74} \*\/."  # noqa: E501

        # correct_header = re.match(val, context.header)
        regex = re.compile(val_no_check_nl, re.DOTALL)
        # correct_header_no_nl = re.match(val_no_check_nl, context.header)
        correct_header_no_nl = regex.search(context.header)
        if correct_header_no_nl is None:
            context.new_error("INVALID_HEADER", context.peek_token(0))
        # else:
        #    print (correct_header.group(1,2,3,4,5,6))

    def run(self, context):
        """
        Header checking. Just a warning for now. Does not trigger moulinette error
        """
        if context.header_parsed is True:
            return False, 0
        elif context.history[-1] == "IsComment" and context.header_parsed is False:
            self.parse_header(context)
            context.header_started = True
        elif context.history[-1] != "IsComment" and context.header_started is True:
            self.check_header(context)
            context.header_parsed = True
        elif (
            context.header_started is False
            and context.header_parsed is False
            and context.history[-1] != "IsComment"
        ):
            context.new_error("INVALID_HEADER", context.peek_token(0))
            context.header_parsed = True
