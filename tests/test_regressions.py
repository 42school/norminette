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


def test_a_comma_in_a_return_separates_two_instructions():
    source = "int\tf(int a)\n{\n\treturn (g(a), 0);\n}\n"
    assert "TOO_MANY_INSTR" in names(check(source))

    nested = "int\tf(int a)\n{\n\treturn (g(a, 0));\n}\n"
    assert "TOO_MANY_INSTR" not in names(check(nested))


def test_every_argument_list_of_a_declaration_wants_void():
    source = "void\t(*f(int a, void (*g)()))(void);\n"
    assert "NO_ARGS_VOID" in names(check(source))

    filled = "void\t(*f(int a, void (*g)(void)))(void);\n"
    assert "NO_ARGS_VOID" not in names(check(filled))


def test_a_sign_and_a_binary_operator_are_told_apart():
    glued = "int\tmain(void)\n{\n\tint\ta;\n\n\ta = a +10;\n\treturn (0);\n}\n"
    assert "SPC_AFTER_OPERATOR" in names(check(glued))

    sign = "int\tmain(void)\n{\n\tint\ta;\n\n\ta = -10;\n\treturn (0);\n}\n"
    assert "SPC_AFTER_OPERATOR" not in names(check(sign))


def test_a_file_ends_with_a_newline():
    assert "NO_NEWLINE_EOF" in names(check("// comment"))
    assert "NO_NEWLINE_EOF" not in names(check("// comment\n"))


def test_a_function_declares_its_return_type():
    assert "MISSING_RETURN_TYPE" in names(check("main(void)\n{\n\treturn (0);\n}\n"))

    typed = "int\tmain(void)\n{\n\treturn (0);\n}\n"
    assert "MISSING_RETURN_TYPE" not in names(check(typed))


def test_a_prototype_name_shares_the_line_of_its_return_type():
    assert "MISSING_TAB_FUNC" in names(check("char\nfoo(void);\n", filename="a.h"))
    assert "MISSING_TAB_FUNC" not in names(check("char\tfoo(void);\n", filename="a.h"))


def test_a_typedef_tag_follows_the_naming_rule():
    wrong = "typedef struct e_x\n{\n\tint\ta;\n}\tt_x;\n"
    assert "STRUCT_TYPE_NAMING" in names(check(wrong, filename="a.h"))

    right = "typedef struct s_x\n{\n\tint\ta;\n}\tt_x;\n"
    assert "STRUCT_TYPE_NAMING" not in names(check(right, filename="a.h"))


def test_a_header_is_protected_from_double_inclusion():
    bare = "int\tf(void);\n"
    assert "HEADER_PROT_MISSING" in names(check(bare, filename="a.h"))

    guarded = "#ifndef A_H\n# define A_H\n\nint\tf(void);\n\n#endif\n"
    assert "HEADER_PROT_MISSING" not in names(check(guarded, filename="a.h"))


def test_a_forward_declaration_takes_a_space():
    assert "TAB_REPLACE_SPACE" in names(check("struct\ts_x;\n", filename="a.h"))
    assert "TAB_REPLACE_SPACE" not in names(check("struct s_x;\n", filename="a.h"))


def test_a_subscript_that_follows_a_call_is_read():
    source = "int\tmain(void)\n{\n\tf(a)[i] = g(x, y);\n\treturn (0);\n}\n"
    assert "PARSING_ERROR" not in names(check(source))


def test_a_split_string_counts_its_physical_lines():
    body = "".join(f"line {i}\\n\\\n" for i in range(30))
    source = 'int\tmain(void)\n{\n\tprintf("' + body + 'end");\n\treturn (0);\n}\n'
    assert "TOO_MANY_LINES" in names(check(source))


def test_a_backslash_separated_from_its_newline_still_splices():
    source = "int\tmain(void)\n{\n\treturn (f(1) \\ \n\t\t\t+ 0);\n}\n"
    reported = names(check(source))
    assert "BAD_LEXEME" not in reported
    assert "SPC_BEFORE_NL" in reported


def test_a_preprocessor_block_may_sit_right_above_a_function():
    body = "int\ta(void)\n{\n\treturn (0);\n}\n\n#ifdef FOO\nint\tb(void)\n{\n\treturn (0);\n}\n#endif\n"
    assert "NL_AFTER_PREPROC" not in names(check(body))

    glued = "int\ta(void)\n{\n\treturn (0);\n}\n#ifdef FOO\nint\tb(void)\n{\n\treturn (0);\n}\n#endif\n"
    assert "NL_AFTER_PREPROC" in names(check(glued))


def test_alignas_is_a_qualifier_not_a_call():
    source = "int\tmain(void)\n{\n\t_Alignas(int) char\tdata[16];\n\n\treturn (0);\n}\n"
    assert names(check(source)) == ["INVALID_HEADER"]


def test_an_initialiser_block_is_indented():
    indented = "int\tg_t[2] = {\n\t{1},\n\t{2}\n};\n"
    assert "TOO_MANY_TAB" not in names(check(indented))

    flat = "int\tg_t[2] = {\n{1},\n{2}\n};\n"
    assert "TOO_FEW_TAB" in names(check(flat))


def test_one_argument_list_keeps_one_indentation():
    body = (
        "\twhile (y--)\n"
        "\t\tif (printf(\n"
        "\t\t\t\t\"%c\",\n"
        "\t\t\t\t(char)(y),\n"
        "\t\t\t(char)(y)\n"
        "\t\t\t) < 0)\n"
        "\t\t\treturn (1);\n"
    )
    source = "int\tmain(int y)\n{\n" + body + "\treturn (0);\n}\n"
    assert "TOO_FEW_TAB" in names(check(source))


def test_a_preprocessor_line_cannot_end_with_a_blank():
    assert "SPC_BEFORE_NL" in names(check("# include <stdio.h> \n"))
    assert "SPC_BEFORE_NL" not in names(check("# include <stdio.h>\n"))


def test_a_define_holds_a_constant_expression():
    assert "PREPROC_CONSTANT" not in names(check("# define SIZE (2 * 4 + 1)\n"))
    assert "PREPROC_CONSTANT" in names(check("# define SIZE 1 1 1\n"))


def test_typeof_is_forbidden():
    source = "int\tmain(void)\n{\n\tint\ta;\n\n\ta = typeof(1);\n\treturn (0);\n}\n"
    assert "TYPEOF_FORBIDDEN" in names(check(source))


def test_a_global_is_reported_whatever_its_form():
    assert "GLOBAL_VAR_DETECTED" in names(check("static int\tg_x;\n"))
    assert "GLOBAL_VAR_DETECTED" in names(check("const int\tg_x = 1;\n"))


def test_one_mistake_is_reported_once():
    long_comment = "\ta = 1;\t/* " + "x" * 90 + " */\n"
    source = "int\tmain(void)\n{\n\tint\ta;\n\n" + long_comment + "\treturn (0);\n}\n"
    reported = names(check(source))
    assert reported.count("LINE_TOO_LONG") == 1
    assert reported.count("COMMENT_ON_INSTR") <= 1


def test_a_multiline_macro_says_so():
    assert "MULTILINE_MACRO" in names(check("#define M 1 \\\n\t+ 2\n"))
    assert "MULTILINE_MACRO" not in names(check("#define M 1\n"))
