import sys
import yaml
import re


def print_yaml(data, exit_code=None):
    print("\n" + yaml.dump(data, width=120))
    if exit_code is not None:
        sys.exit(exit_code)


def print_text(text, exit_code=None, prefix=None):

    if prefix is None:
        prefix = "[!] " if exit_code else "[+] "

    for line in text.split("\n"):
        print(prefix + line)
        prefix = "... "

    if exit_code is not None:
        sys.exit(exit_code)


def ask_for_confirmation(prompt):
    while True:
        answer = input(f"[?] {prompt} [yes/no] ").lower()

        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False

        print_text("Please type either 'yes' or 'no'", prefix="[!] ")


def get_next_free_name_like(wanted, existing):
    try:
        if wanted not in existing:
            return wanted

        return next(f"{wanted}{i}" for i
                    in range(2, 256)
                    if f"{wanted}{i}" not in existing)

    except StopIteration:
        return None


def as_pattern(name):

    if name is None:
        return None

    name = re.escape(name)
    name = name.replace("\\*", ".*")
    name = name.replace("\\?", ".")

    return re.compile(f"^{name}$")


def as_literal(name):

    if name is None:
        return None

    return re.compile(re.escape(name))
