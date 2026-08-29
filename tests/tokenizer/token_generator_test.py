import glob
import os

import pytest

from norminette.file import File
from norminette.lexer import Lexer
from norminette.registry import Registry


registry = Registry()
samples = os.path.join(os.path.dirname(__file__), "samples", "ok")
test_files = sorted(glob.glob(os.path.join(samples, "*.[ch]")))
assert test_files, f"no sample found in {samples!r}"


@pytest.mark.parametrize("file", test_files)
def test_rule_for_file(file):
    with open(f"{os.path.splitext(file)[0]}.tokens") as out_file:
        out_content = out_file.read()

    lexer = Lexer(File(file))

    output = ''
    tokens = list(lexer)
    if tokens:
        for token in tokens:
            output += str(token) + '\n' * int(token.type == "NEWLINE")
        if tokens[-1].type != "NEWLINE":
            output += "\n"

    assert output == out_content
