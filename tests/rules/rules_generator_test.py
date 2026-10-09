import glob
import os

import pytest

from norminette.file import File
from norminette.lexer import Lexer
from norminette.context import Context
from norminette.registry import Registry
from norminette.errors import HumanizedErrorsFormatter


registry = Registry()
samples = os.path.join(os.path.dirname(__file__), "samples")
test_files = sorted(glob.glob(os.path.join(samples, "*.[ch]")))
assert test_files, f"no sample found in {samples!r}"


@pytest.mark.parametrize("file", test_files)
def test_rule_for_file(file, capsys):
    with open(file, "r") as test_file:
        file_to_lex = test_file.read()

    with open(f"{os.path.splitext(file)[0]}.out") as out_file:
        out_content = out_file.read()

    file = File(file, file_to_lex)
    lexer = Lexer(file)
    context = Context(file, list(lexer), debug=2)
    registry.run(context)
    errors = HumanizedErrorsFormatter(file, use_colors=False)
    print(errors, end='')
    captured = capsys.readouterr()

    assert captured.out == out_content
