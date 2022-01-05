import argparse
import re
from pathlib import Path
import subprocess
from typing import Optional, Sequence
import json
from datetime import datetime

ROOT_PATH = Path(".").resolve()
COMMIT_ACTIONS_PATH = ROOT_PATH.joinpath("commits_actions.json")
PROGRESS_PATH = ROOT_PATH.joinpath("progress.md")
# parser = argparse.ArgumentParser(description='Commit changes to git')
# parser.add_argument('commit', metavar='commit', type=str, help='commit message')
# args = parser.parse_args()
# commit_message = args.commit
commit_message = "+ tool to commit changes to git;+ add modification;+ delete;+ modify;+ write to progress;+ commit all python files;w ;c "
if not COMMIT_ACTIONS_PATH.is_file():
    f = open(COMMIT_ACTIONS_PATH, "w")
    f.write("[]")
    f.close()
if not PROGRESS_PATH.is_file():
    f = open(PROGRESS_PATH, "w")
    f.write(f"# Progress of {ROOT_PATH.name}\n")
    f.close()


def parse_printer_format_range(string: str) -> Sequence[int]:
    string = string.split(",")  # type: ignore
    values = []
    for s in string:
        try:
            value = int(s)
            value = [value]
        except ValueError:
            value = s.split("-")
            value = list(range(int(value[0]), int(value[1])+1))
        values.extend(value)
    return values


def parse_add(string: str, buffer: list, *args, **kwargs):
    buffer.append(string)


def parse_delete(string: str, buffer: list, *args, **kwargs):
    match_del = re.match("(^[0-9-,]+).*", string)
    if match_del:
        del_range = match_del.group(0)
        del_range = parse_printer_format_range(del_range)
        for i in del_range:
            buffer.pop(i)
    else:
        print(f"WARNING: Could not parse delete action {string}")


def parse_modify(string: str, buffer: list, *args, **kwargs):
    match_mod = re.match("(^[0-9-,]+) (.*)", string)
    if match_mod:
        mod_range = match_mod.group(0)
        parse_delete(mod_range, buffer)
        parse_add(match_mod.group(1), buffer)
    else:
        print(f"WARNING: Could not parse modify action {string}")


def show_buffer():
    for i, e in enumerate(buffer):
        print(f"{i}: {e}")


def formatted_current_date() -> str:
    return datetime.now().strftime("%a %B %d %Y")


def get_commit_hash(short: bool = True):
    args = ["git", "rev-parse", "--short", "HEAD"]
    if not short:
        args = [arg for arg in args if "short" not in arg]
    return subprocess.check_output(args).decode("utf-8").strip()

def get_repo_url(long_commit_hash: Optional[str] = None) -> str:
    args = ["git", "config", "--get", "remote.origin.url"]
    root_path = re.match("^(.*).git",subprocess.check_output(args).decode("utf-8").strip())
    if root_path is not None:
        root_path = root_path.group(1)
    else:
        raise Exception("Could not get root path of git repo: are you at the root of the repo?")
    if long_commit_hash is not None:
        root_path = f"{root_path}/tree/{long_commit_hash}"
    return root_path

def get_text_summary() -> str:
    return ','.join(buffer)

def write_to_progress(buffer: list, *args, **kwargs):
    # Check with a regex if the current date is currently in the progress file
    with open(PROGRESS_PATH, "r") as f:
        content = f.read()
    if not re.match(f"\n## {formatted_current_date()}", content):
        with open(PROGRESS_PATH, "a") as f:
            f.write(f"\n## {formatted_current_date()}\n")
    # write the buffer to the progress file
    with open(PROGRESS_PATH, "a") as f:
        f.write(f"\n- [{get_commit_hash()}]({get_repo_url(get_commit_hash(short=False))}) {get_text_summary()}")

def commit_current_state(*args,**kwargs):
    subprocess.check_call(["git", "add", ":/*.py"])
    subprocess.check_call(["git","commit", "-m", get_text_summary()])
# process commit message
# get splited actions separated by ';' in a list
actions = commit_message.split(';')
identificators = {
    "-": parse_delete,
    "+": parse_add,
    "m": parse_modify,
    "w": write_to_progress,
    "c": commit_current_state
}
with open(COMMIT_ACTIONS_PATH, "r") as f:
    buffer = json.load(f)
for i in range(len(actions)):
    action = actions[i]
    dico_action = {}
    match = re.match(f"(^[{''.join(identificators)}])( )(.*)", action)
    if match:
        for identifier, fun_parser in identificators.items():
            if match.group(1) == identifier:
                fun_parser(string=match.group(3), buffer=buffer)
    else:
        raise ValueError("Invalid commit message")

with open(COMMIT_ACTIONS_PATH, "w") as f:
    json.dump(buffer, f)
