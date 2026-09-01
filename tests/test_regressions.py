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


def test_a_binary_file_is_reported_not_raised(tmp_path):
    path = tmp_path / "binary.c"
    path.write_bytes(bytes(range(256)) * 16)
    result = norminette(str(path))
    assert "PARSING_ERROR" in result.stdout
    assert "Traceback" not in result.stderr
    assert result.returncode == 1


def test_an_unterminated_char_is_reported_not_raised(tmp_path):
    path = tmp_path / "quote.c"
    path.write_text("int\tmain(void)\n{\n\tchar c = '" + "a" * 300 + "\n}\n")
    result = norminette(str(path))
    assert "PARSING_ERROR" in result.stdout
    assert result.returncode == 1


def test_json_survives_a_file_that_cannot_be_parsed(tmp_path):
    path = tmp_path / "binary.c"
    path.write_bytes(bytes(range(256)) * 16)
    result = norminette("--format", "json", str(path))
    assert json.loads(result.stdout)["files"][0]["status"] == "Error"


def test_a_const_argument_does_not_excuse_the_declaration(tmp_path):
    source = "int\tmain(void)\n{\n\tvoid\t(*f)(const char *) = 0;\n\n\treturn (f != 0);\n}\n"
    assert "DECL_ASSIGN_LINE" in names(check(source))

    excused = "int\tmain(void)\n{\n\tvoid\t(*const f)(int) = 0;\n\n\treturn (f != 0);\n}\n"
    assert "DECL_ASSIGN_LINE" not in names(check(excused))


def test_an_unsupported_extension_does_not_hide_the_others(tmp_path):
    (tmp_path / "Makefile").write_text("all:\n")
    good = write(tmp_path, "good.c", "int\tmain(void)\n{\n\treturn (0);\n}\n")

    result = norminette(str(tmp_path / "Makefile"), good)
    assert "is not valid C or C header file" in result.stdout
    assert "good.c: OK!" in result.stdout
    assert result.returncode == 1


def test_an_address_argument_is_still_a_call():
    source = (
        "void\tf(char *d, char *s1, char *s2)\n{\n"
        "\tft_strlcpy(&d[ft_strlen(s1)], s2, 1);\n}\n"
    )
    assert "VAR_DECL_START_FUNC" not in names(check(source))

    declaration = "void\tf(void)\n{\n\tt_example\t(*fp)(void);\n\n\tfp = 0;\n}\n"
    assert "TAB_INSTEAD_SPC" not in names(check(declaration))


def test_a_constant_expression_is_not_a_pointer():
    source = "int\tmain(void)\n{\n\tdouble\tx;\n\n\tx = (double)(90 / 640) * 6;\n\treturn ((int)x);\n}\n"
    assert "SPC_AFTER_POINTER" not in names(check(source))

    pointer = "int\tmain(int *p)\n{\n\tint\tx;\n\n\tx = (int) * p;\n\treturn (x);\n}\n"
    assert "SPC_AFTER_POINTER" in names(check(pointer))


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
    body = 'int\tmain(void)\n{\n\treturn ("\\q"[0]);\n}\n'
    path = write(tmp_path, "notice.c", body)
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


def test_allow_globals_keeps_the_naming_rule(tmp_path):
    path = write(tmp_path, "gl.c", "int\tg_ok = 1;\nint\tbad_name = 2;\n")

    default = norminette(path)
    assert "GLOBAL_VAR_DETECTED" in default.stdout
    assert "GLOBAL_VAR_NAMING" in default.stdout

    allowed = norminette("--allow-globals", path)
    assert "GLOBAL_VAR_DETECTED" not in allowed.stdout
    assert "GLOBAL_VAR_NAMING" in allowed.stdout


def test_allow_globals_clears_a_well_named_global(tmp_path):
    path = write(tmp_path, "gl.c", "int\tg_ok = 1;\n")
    assert "GLOBAL_VAR_DETECTED" in norminette(path).stdout
    assert norminette("--allow-globals", path).stdout.strip() == "gl.c: OK!"


def test_only_errors_hides_the_files_with_nothing_to_say(tmp_path):
    clean = write(tmp_path, "clean.c", "int\tmain(void)\n{\n\treturn (0);\n}\n")
    broken = write(tmp_path, "broken.c", "int\tmain(void)\n{\n\treturn (0)\n}\n")

    full = norminette(clean, broken)
    assert "clean.c: OK!" in full.stdout

    quiet = norminette("--only-errors", clean, broken)
    assert "clean.c" not in quiet.stdout
    assert "broken.c" in quiet.stdout
    assert quiet.returncode == full.returncode


def test_only_errors_leaves_json_complete(tmp_path):
    clean = write(tmp_path, "clean.c", "int\tmain(void)\n{\n\treturn (0);\n}\n")
    result = norminette("--format", "json", "--only-errors", clean)
    assert len(json.loads(result.stdout)["files"]) == 1


def test_a_dash_reads_the_file_from_stdin(tmp_path):
    source = HEADER.format(name="stdin.c") + "int\tmain(void)\n{\n\treturn (0);\n}\n"
    result = subprocess.run(
        [sys.executable, "-m", "norminette", "-", "--filename", "stdin.c"],
        input=source,
        capture_output=True,
        text=True,
    )
    assert "stdin.c: OK!" in result.stdout
    assert result.returncode == 0


def test_an_unsupported_extension_is_a_failure(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("hello\n")
    assert norminette(str(path)).returncode == 1
