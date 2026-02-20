from norminette.tools.normignore import NormIgnoreSpec
import pytest


def test_single_file(tmp_path):
    normignore_file = tmp_path / ".normignore"
    normignore_file.write_text("ignored.c\n")

    file1 = tmp_path / "ignored.c"
    file2 = tmp_path / "not_ignored.c"
    file1.write_text("")
    file2.write_text("")

    ignore = NormIgnoreSpec(tmp_path)

    files = [file1, file2]
    filtered = [f for f in files if not ignore.is_ignored(f)]
    assert file2 in filtered
    assert file1 not in filtered


def test_directory(tmp_path):
    normignore_file = tmp_path / ".normignore"
    normignore_file.write_text("build/\n")

    (tmp_path / "build").mkdir()
    file1 = tmp_path / "build" / "file.c"
    file1.write_text("")
    file2 = tmp_path / "main.c"
    file2.write_text("")

    ignore = NormIgnoreSpec(tmp_path)
    files = [file1, file2]
    filtered = [f for f in files if not ignore.is_ignored(f)]

    assert file2 in filtered
    assert file1 not in filtered


@pytest.mark.parametrize("pattern, filename, ignored", [
    ("*.c", "main.c", True),
    ("*.c", "readme.md", False),
    ("build/", "build/file.c", True),
    ("build/", "src/file.c", False),
])
def test_multiple_patterns(tmp_path, pattern, filename, ignored):
    (tmp_path / ".normignore").write_text(pattern + "\n")
    file = tmp_path / filename
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("")

    ignore = NormIgnoreSpec(tmp_path)
    result = ignore.is_ignored(file)
    assert result == ignored
