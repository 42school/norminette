import glob
import sys
import pathlib
import platform
from importlib.metadata import version

import argparse
from norminette.errors import formatters
from norminette.file import File
from norminette.lexer import Lexer
from norminette.exceptions import CParsingError
from norminette.registry import Registry
from norminette.context import Context
from norminette.tools.colors import colors

import subprocess

version_text = "norminette" + version("norminette")
version_text += f", Python {platform.python_version()}"
version_text += f", {platform.platform()}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        help="File(s) or folder(s) you wanna run the parser on. If no file provided, runs on current folder.",
        nargs="*",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="count",
        help="Debug output (-dd outputs the whole tokenization and such, used for developping)",
        default=0,
    )
    parser.add_argument(
        "-o",
        "--only-filename",
        action="store_true",
        help="By default norminette displays the full path to the file, this allows to show only filename",
        default=False,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=version_text,
    )
    parser.add_argument(
        "--cfile",
        action="store",
        help="Store C file content directly instead of filename",
    )
    parser.add_argument(
        "--hfile",
        action="store",
        help="Store header file content directly instead of filename",
    )
    parser.add_argument(
        "--filename",
        action="store",
        help="Stores filename if --cfile or --hfile is passed",
    )
    parser.add_argument(
        "--use-gitignore",
        action="store_true",
        help="Parse only source files not match to .gitignore",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=list(formatter.name for formatter in formatters),
        help="formatting style for errors",
        default="humanized",
    )
    parser.add_argument("--no-colors", action="store_true", help="Disable colors in output")
    parser.add_argument("-R", nargs=1, help="compatibility for norminette 2")
    args = parser.parse_args()
    registry = Registry()

    format = next(filter(lambda it: it.name == args.format, formatters))
    files = []
    debug = args.debug
    if args.cfile or args.hfile:
        file_name = args.filename or ("file.c" if args.cfile else "file.h")
        file_data = args.cfile if args.cfile else args.hfile
        file = File(file_name, file_data)
        files.append(file)
    else:
        stack = []
        stack += args.file if args.file else glob.glob("**/*.[ch]", recursive=True)
        for item in stack:
            path = pathlib.Path(item)
            if not path.exists():
                print(f"Error: '{path!s}' no such file or directory")
                sys.exit(1)
            if path.is_file():
                if path.suffix not in (".c", ".h"):
                    print(f"Error: {path.name!r} is not valid C or C header file")
                else:
                    file = File(item)
                    files.append(file)
            if path.is_dir():
                stack += glob.glob(str(path) + "/**/*.[ch]", recursive=True)
        del stack

    if args.use_gitignore:
        tmp_targets = []
        for target in files:
            command = ["git", "check-ignore", "-q", target.path]
            exit_code = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
            """
            see: $ man git-check-ignore
            EXIT STATUS
                  0: One or more of the provided paths is ignored.
                  1: None of the provided paths are ignored.
                128: A fatal error was encountered.
            """
            if exit_code == 0:
                pass
            elif exit_code == 1:
                tmp_targets.append(target)
            elif exit_code == 128:
                print(f'Error: something wrong with --use-gitignore option {target.path!r}')
                sys.exit(0)
        files = tmp_targets
    for file in files:
        try:
            lexer = Lexer(file)
            tokens = list(lexer)
            context = Context(file, tokens, debug, args.R)
            registry.run(context)
        except CParsingError as e:
            print(file.path + f": Error!\n\t{colors(e.msg, 'red')}")
            sys.exit(1)
        except KeyboardInterrupt:
            sys.exit(1)
    errors = format(files, use_colors=not args.no_colors)
    print(errors, end='')
    sys.exit(1 if len(file.errors) else 0)


if __name__ == "__main__":
    main()
