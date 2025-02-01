import pytest
import glob

from norminette.file import File
from norminette.lexer import Lexer
from norminette.context import Context
from norminette.registry import Registry
from norminette.errors import ShortErrorsFormatter


registry = Registry()
test_files = glob.glob("tests/rules/samples/*.[ch]")


@pytest.mark.parametrize("file", test_files)
def test_rule_for_file(file, capsys):
    with open(file, "r") as test_file:
        file_to_lex = test_file.read()

    with open(f"{file.split('.')[0]}.out") as out_file:
        out_content = out_file.read()

    file = File(file, file_to_lex)
    lexer = Lexer(file)
    context = Context(file, list(lexer), debug=2)
    registry.run(context)
    errors = ShortErrorsFormatter(file)
    print(errors, end='')
    captured = capsys.readouterr()

    assert captured.out == out_content
