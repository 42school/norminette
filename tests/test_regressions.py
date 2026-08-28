import json
import subprocess
import sys

import pytest

from norminette.context import Context
from norminette.exceptions import CParsingError
from norminette.file import File
from norminette.i18n import set_locale
from norminette.lexer import Lexer
from norminette.registry import Registry

HEADER = """\
/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   {name:<51}:+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: norm <norm@42.fr>                          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2025/01/01 00:00:00 by norm              #+#    #+#             */
/*   Updated: 2025/01/01 00:00:00 by norm             ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

"""


def check(source, *, filename="test.c", added_value=None):
    file = File(filename, source)
    Registry().run(Context(file, list(Lexer(file)), added_value=added_value))
    return file


def names(file):
    return [error.name for error in file.errors]


def test_set_locale_is_quiet(capsys):
    set_locale("en_US")
    assert capsys.readouterr().out == ""


def test_unmatched_lexemes_do_not_recurse():
    file = File("test.c", "int\tmain(void)\n{\n\t" + "@" * 5000 + "\n}\n")
    list(Lexer(file))
    assert names(file) == ["BAD_LEXEME"] * 5000


def test_source_accepts_non_utf8_bytes(tmp_path):
    path = tmp_path / "latin1.c"
    path.write_bytes(b"int\tmain(void)\n{\n\t// caf\xe9\n\treturn (0);\n}\n")
    assert "int" in File(str(path)).source


def test_peek_token_rejects_negative_index():
    file = File("test.c", "int\tmain(void);\n")
    context = Context(file, list(Lexer(file)))
    assert context.peek_token(-1) is None
    assert context.peek_token(-5000) is None


def test_truncated_prototype_reports_a_parsing_error():
    with pytest.raises(CParsingError):
        check("int a(int b)", filename="test.h")


def test_a_line_holding_only_a_space_at_eof_is_not_a_crash():
    file = check("void\tfn(int a)\n ")
    assert "INVALID_HEADER" in names(file)


def test_ternary_is_allowed_in_a_define_only():
    define = check("# define FOO (1 ? 2 : 3)\n", added_value=["CheckDefine"])
    assert "TERNARY_FBIDDEN" not in names(define)

    source = "int\tmain(void)\n{\n\tint\tdefine;\n\n\tdefine = 1;\n\treturn (define ? 2 : 3);\n}\n"
    variable = check(source, added_value=["CheckDefine"])
    assert "TERNARY_FBIDDEN" in names(variable)


def test_long_comment_does_not_move_the_comment_token():
    source = "int\tmain(void)\n{\n\t/*\n\t** " + "A" * 90 + "\n\t*/\n\treturn (0);\n}\n"
    file = check(source)
    scopes = [it for it in file.errors if it.name == "WRONG_SCOPE_COMMENT"]
    assert [(it.highlights[0].lineno, it.highlights[0].column) for it in scopes] == [(3, 5)]


def norminette(*args):
    return subprocess.run(
        [sys.executable, "-m", "norminette", *args],
        capture_output=True,
        text=True,
    )


def write(directory, name, body):
    path = directory / name
    path.write_text(HEADER.format(name=name) + body)
    return str(path)


def test_a_file_holding_only_notices_exits_zero(tmp_path):
    path = write(tmp_path, "notice.c", 'char\t*g_a = "\\q";\n')
    result = norminette(path)
    assert "notice.c: OK!" in result.stdout
    assert "Notice: UNKNOWN_ESCAPE" in result.stdout
    assert result.returncode == 0


def test_a_broken_file_does_not_hide_the_others(tmp_path):
    first = write(tmp_path, "first.c", "int\tmain(void)\n{\n\treturn (0)\n}\n")
    broken = write(tmp_path, "broken.c", "int\tmain(void)\n{\n\t)(}{;\n}\n")
    last = write(tmp_path, "last.c", "int\tmain(void)\n{\n\treturn (0);\n}\n")

    result = norminette(first, broken, last)
    assert "first.c:" in result.stdout
    assert "broken.c:" in result.stdout
    assert "last.c: OK!" in result.stdout
    assert result.returncode == 1


def test_json_output_holds_nothing_but_json(tmp_path):
    path = write(tmp_path, "broken.c", "int\tmain(void)\n{\n\t)(}{;\n}\n")
    result = norminette("--format", "json", path)
    assert json.loads(result.stdout)["files"][0]["status"] == "Error"


def test_an_unsupported_extension_is_a_failure(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("hello\n")
    assert norminette(str(path)).returncode == 1
