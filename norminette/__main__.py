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
        help="File(s) or folder(s) you want to run the parser on. If no file provided, runs on current folder.",
        nargs="*",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="count",
        help="Debug output (-dd outputs the whole tokenization and such, used for developing)",
        default=0,
    )
    parser.add_argument(
        "-o",
        "--only-filename",
        action="store_true",
        help="By default norminette displays the full path to the file, this allows showing only filename",
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
        help="Parse only source files not matched to .gitignore",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=[formatter.name for formatter in formatters],
        help="Formatting style for errors",
        default="humanized",
    )
    parser.add_argument("-R", nargs=1, help="compatibility for norminette 2")
    args = parser.parse_args()
    
    registry = Registry()

    format = next(filter(lambda it: it.name == args.format, formatters))
    files = []
    debug = args.debug
    has_err = False
    
    if args.cfile or args.hfile:
        file_name = args.filename or ("file.c" if args.cfile else "file.h")
        file_data = args.cfile if args.cfile else args.hfile
        file = File(file_name, file_data)
        files.append(file)
    else:
        stack = []
        stack.extend(args.file if args.file else glob.glob("**/*.[ch]", recursive=True))
        visited_paths = set()

        while stack:
            item = stack.pop()
            path = pathlib.Path(item).resolve()

            if path in visited_paths:
                continue
            visited_paths.add(path)

            if not path.exists():
                print(f"Error: '{path}' no such file or directory")
                sys.exit(1)

            if path.is_file():
                if path.suffix not in (".c", ".h"):
                    print(f"Error: {path.name} is not a valid C or C header file")
                else:
                    file = File(str(path))
                    files.append(file)
            elif path.is_dir():
                stack.extend(glob.glob(str(path) + "/**/*.[ch]", recursive=True))

    if args.use_gitignore:
        tmp_targets = []
        for target in files:
            command = ["git", "check-ignore", "-q", target.path]
            exit_code = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode

            if exit_code == 0:
                continue
            elif exit_code == 1:
                tmp_targets.append(target)
            elif exit_code == 128:
                print(f'Error: something wrong with --use-gitignore option {target.path}')
                sys.exit(1)
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
        except Exception as e:
            print(f"Unexpected error: {e}")
            has_err = True
            events[-1].set()

    errors = format(files)
    print(errors, end='')
    sys.exit(1 if any(file.errors for file in files) else 0)

if __name__ == "__main__":
    main()
