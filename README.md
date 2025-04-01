# norminette for 42 schools

## Install

Requires python3.8+ (3.8, 3.9, 3.10, 3.11)

### Directly inside your global commands

Install using pip.
```shell
python3 -m pip install --upgrade pip setuptools
python3 -m pip install norminette
```

Install using pipx.
```shell
sudo apt update
sudo apt install python3-setuptools
sudo apt install pipx
pipx install norminette
pipx ensurepath
```

Install using a virtual environment.
```shell
python3 -m venv $HOME/.venv
source $HOME/.venv/bin/activate
python3 -m pip install --upgrade pip setuptools
python3 -m pip install norminette
echo "export PATH=\$PATH:$HOME/.venv/bin" >> $HOME/.${SHELL##/bin/}rc
deactivate
```

To upgrade an existing install, use
```shell
python3 -m pip install --upgrade norminette
```

## Usage

- Runs on the current folder and any subfolder:

```
norminette
```

- Runs on the given filename(s):

```
norminette filename.[c/h]
```

- Prevents stopping on various blocking errors:

```
norminette -d
```

- Outputs all the debug logging:

```
norminette -dd
```

## Docker usage

```
docker build -t norminette .
cd ~/42/ft_printf
docker run --rm -v $PWD:/code norminette
```

If you encounter an error or an incorrect output, you can:
 - Open an issue on github
 - Post a message on the dedicated slack channel (#norminette-v3-beta)


Please try to include as much information as possible (the file on which it crashed, etc)

Feel free to do pull requests if you want to help as well. Make sure that run_test.sh properly runs after your modifications.

## Run for development

This new version uses poetry as a dependency manager.

If you want to contribute:

```shell
poetry install

# Run dev norminette
poetry run norminette

# Or... with virtual env
source .venv/bin/activate
norminette

# Run tests
poetry run pytest
```

## Github action

Workflow example to check code with github action :

```yaml
---
name: Norminette

on:
  push:

jobs:
  check-norminette:
    name: Norminette
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Norminette
        uses: 42School/norminette@<tag>
        with:
          args: '-RCheckForbiddenSourceHeader'
```
