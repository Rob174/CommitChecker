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
commit_message = "+ save internal files at the end;w "
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

def save_internals():
    for internal_file in internal_files:
        subprocess.check_call(["git", "add", internal_file])
    subprocess.check_call(["git","commit", "-m", "Update progress files"])

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

def path_url_main_repo():
    args = ["git", "config", "--get", "remote.origin.url"]
    root_path = re.match("^(.*).git",subprocess.check_output(args).decode("utf-8").strip())
    if root_path is not None:
        root_path = root_path.group(1)
    else:
        raise Exception("Could not get root path of git repo: are you at the root of the repo?")
    return root_path

def get_repo_url(long_commit_hash: Optional[str] = None) -> str:
    root_path = path_url_main_repo()
    if long_commit_hash is not None:
        root_path = f"{root_path}/tree/{long_commit_hash}"
    return root_path

def write_to_progress(buffer: list, *args, **kwargs):
    commit_changes(buffer, *args, **kwargs)
    # Check with a regex if the current date is currently in the progress file
    with open(PROGRESS_PATH, "r") as f:
        content = f.read()
    if re.search(f"\n## {formatted_current_date()}", content) is None:
        with open(PROGRESS_PATH, "a") as f:
            f.write(f"\n## {formatted_current_date()}\n")
    # write the buffer to the progress file
    with open(PROGRESS_PATH, "a") as f:
        f.write(f"\n- [{get_commit_hash()}]({get_repo_url(get_commit_hash(short=False))}) {format_current_changes()}")

def commit_current_state(*args,**kwargs):
    subprocess.check_call(["git", "add", ":/*.py", ":/*.md"])
    subprocess.check_call(["git","commit", "-m", format_current_changes()])
    
def format_current_changes():
    visible_modifications = [m for m,dico_m in identificators.items() if not dico_m["commit_hidden"]]
    for to_escape in ["+"]:
        visible_modifications = [m.replace(to_escape, "\\"+to_escape) for m in visible_modifications]
    commit_message_splited = [c for c in commit_message.split(";") if re.match(f"^{'|'.join(visible_modifications)} ",c)]
    return ";".join(commit_message_splited)
    
def commit_changes(*args,**kwargs):
    subprocess.check_call(["git", "add", ":/*.py", ":/*.md"])
    args = ["git", "commit"]
    changes = format_current_changes()
    if changes != '':
        args.append("-m")
        args.append(changes)
    subprocess.check_call(args)
    
def update_last_commit(*args,**kwargs):
    with open(PROGRESS_PATH) as f:
        content = f.readlines()
    last_line = content[-1]
    # 32 = len("[short_commit_hash](https://github.com/) + 3* "/" (1 for pseudo/repo, 1 for repo/tree, 1 for the end)
    last_line = re.sub(f"- [^)]{32,}(.*)", f"- [{get_commit_hash()}]({get_repo_url(get_commit_hash(short=False))}) \\2", last_line)
    content[-1] = last_line
    with open(PROGRESS_PATH,"w") as f:
        f.writelines(content)
# process commit message
# get splited actions separated by ';' in a list
actions = commit_message.split(';')
identificators = {
    "-": {"fn":parse_delete, "commit_hidden":False},
    "+": {"fn":parse_add, "commit_hidden":False},
    "m": {"fn":parse_modify, "commit_hidden":False},
    "w": {"fn":write_to_progress, "commit_hidden":True},
    "c": {"fn":commit_current_state, "commit_hidden":True},
    "cc":{"fn":commit_changes, "commit_hidden":True},
    "u": {"fn":update_last_commit, "commit_hidden":True}
}
internal_files = ["progress.md","commits_actions.json"]
with open(COMMIT_ACTIONS_PATH, "r") as f:
    buffer = json.load(f)
for i in range(len(actions)):
    action = actions[i]
    dico_action = {}
    match = action.split()[0]
    remaining = action[len(match):]
    if match in identificators:
        identificators[match]["fn"](remaining, buffer)
    else:
        raise ValueError("Invalid commit message")

with open(COMMIT_ACTIONS_PATH, "w") as f:
    json.dump(buffer, f)

save_internals()
