import os
import subprocess
import sys
from pathlib import Path
from importlib.metadata import version
from typing import List


__all__ = (
    "set_locale",
    "get_env_locale",
    "_",
)

LOCALES = (
    "en_US",
    "pt_BR",
)

LOCALE_DIR = Path(__file__).parent / "locale"

DOMAIN = "norminette"

# Default fallback
_ = lambda _: _  # noqa: E731


def set_locale(locale: str) -> None:
    """
    Set the locale for the application.
    This function loads the translation files from the locale directory and sets the translation function.
    """
    print(f"Setting locale to {locale}")
    global _
    try:
        import gettext

        translation = gettext.translation(
            DOMAIN,
            localedir=str(LOCALE_DIR),
            languages=[locale],
            fallback=True,
        )
        _ = translation.gettext
    except ImportError:
        raise


def get_env_locale(default: str = "en_US") -> str:
    """
    Get the locale from the environment.
    This function returns the locale based on the LANGUAGE environment variable.
    """
    keys = (
        "NORMINETTE_LOCALE",
        "LOCALE",
    )
    for key in keys:
        locale = os.environ.get(key)
        if locale:
            return locale.split(":")[0]
    return default


def _get_pot_file_path() -> Path:
    """
    Get the path to the .pot file.
    This function returns the path to the .pot file in the locale directory.
    """
    return LOCALE_DIR / f"{DOMAIN}.pot"


def _collect_python_files(root_dir: Path) -> List[Path]:
    """
    Collect all Python source files from the given root directory.
    """
    return [file for file in root_dir.rglob("norminette/**/*.py")]


def _create_pot_file() -> None:
    """
    Create the .pot file by extracting translatable strings from Python source files.
    """
    root_dir = Path(__file__).parent.parent
    source_files = _collect_python_files(root_dir)

    try:
        result = subprocess.run(
            [
                "xgettext",
                "-o",
                str(_get_pot_file_path()),
                "--from-code=UTF-8",
                "--keyword=_",
            ] + [str(file.relative_to(root_dir)) for file in source_files],
            check=True,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            _update_pot_header(_get_pot_file_path())
            print("Successfully created .pot file.")
        else:
            print(f"xgettext exited with code {result.returncode}.")
            print(f"Error output: {result.stderr}")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error while running xgettext: {e}")
        print(f"Output: {e.output}")
        sys.exit(1)


def _create_or_update_po_files() -> None:
    """
    Create or update .po files for each locale.
    This function creates or updates .po files for each locale defined in the LOCALES list
    using the .pot file as a template and placing them in the correct locale directory.
    """
    pot_file = _get_pot_file_path()
    if not pot_file.exists():
        print("Error: .pot file not found. Run _create_pot_file() first.")
        sys.exit(1)

    for locale in LOCALES:
        locale_path = LOCALE_DIR / locale / "LC_MESSAGES"
        locale_path.mkdir(parents=True, exist_ok=True)

        po_file = locale_path / f"{DOMAIN}.po"

        if po_file.exists():
            try:
                # Merge existing .po file with the updated .pot file
                result = subprocess.run(
                    ["msgmerge", "--update", "--backup=none", str(po_file), str(pot_file)],
                    check=True,
                    text=True,
                    stderr=subprocess.STDOUT,
                )
                if result.returncode == 0:
                    print(f"Successfully updated {locale} .po file")
                    _update_po_header(po_file)
                else:
                    print(f"Error updating {locale} .po file:")
                    print(result.stdout)
                    print(result.stderr)
                    sys.exit(1)
            except subprocess.CalledProcessError as e:
                print(f"Error while updating {locale} .po file: {e}")
                print(f"Output: {e.output}")
                sys.exit(1)
        else:
            try:
                # Initialize .po file from .pot template
                result = subprocess.run(
                    ["msginit", "--no-translator",
                     "--input", str(pot_file),
                     "--output-file", str(po_file),
                     "--locale", locale],
                    check=True,
                    text=True,
                    stderr=subprocess.STDOUT,  # Redirect stderr to stdout
                )
                if result.returncode == 0:
                    print(f"Successfully created {locale} .po file")
                    _update_po_header(po_file)
                else:
                    print(f"Error creating {locale} .po file.")
                    print(result.stderr)
                    print(result.stdout)
                    sys.exit(1)
            except subprocess.CalledProcessError as e:
                print(f"Error while creating {locale} .po file: {e}")
                print(f"Output: {e.output}")
                sys.exit(1)


def _update_pot_header(pot_file: Path) -> None:
    """
    Update the header of the .pot file to set the charset to UTF-8 and update other metadata.
    """
    project_version = version("norminette")
    try:
        with pot_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        with pot_file.open("w", encoding="utf-8") as f:
            for line in lines:
                if "Content-Type:" in line:
                    f.write('"Content-Type: text/plain; charset=UTF-8\\n"\n')
                elif "Project-Id-Version:" in line:
                    f.write(f'"Project-Id-Version: {project_version}\\n"\n')
                else:
                    f.write(line)

        print(f"Updated header of {pot_file} with charset=UTF-8 and version={project_version}.")
    except Exception as e:
        print(f"Error while updating .pot header: {e}")
        sys.exit(1)


def _update_po_header(po_file: Path) -> None:
    """
    Update the header of the .po file to set the project version and other metadata.
    """
    project_version = version("norminette")
    try:
        with po_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        with po_file.open("w", encoding="utf-8") as f:
            for line in lines:
                if "Project-Id-Version:" in line:
                    f.write(f'"Project-Id-Version: {project_version}\\n"\n')
                else:
                    f.write(line)

        print(f"Updated header of {po_file} with version={project_version}.")
    except Exception as e:
        print(f"Error while updating .po header: {e}")
        sys.exit(1)


def _compile_mo_files() -> None:
    """
    Compile .po files into .mo files for each locale.
    This function compiles the .po files into .mo files, which are used by gettext for translations.
    """
    for locale in LOCALES:
        po_file = LOCALE_DIR / locale / "LC_MESSAGES" / f"{DOMAIN}.po"
        mo_file = LOCALE_DIR / locale / "LC_MESSAGES" / f"{DOMAIN}.mo"

        if po_file.exists():
            try:
                result = subprocess.run(
                    ["msgfmt", str(po_file), "-o", str(mo_file)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    print(f"Successfully compiled {locale} .mo file")
                else:
                    print(f"Error compiling {locale} .mo file: {result.stderr}")
                    sys.exit(1)
            except subprocess.CalledProcessError as e:
                print(f"Error while compiling {locale} .mo file: {e}")
                print(f"Output: {e.output}")
                sys.exit(1)
        else:
            print(f"Warning: .po file for {locale} does not exist. Skipping compilation.")


set_locale(get_env_locale())


if __name__ == "__main__":
    try:
        _create_pot_file()
        _create_or_update_po_files()
        _compile_mo_files()
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
