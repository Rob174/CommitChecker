from pathlib import Path
import subprocess
from typing import List, Optional
import tensorflow as tf
from time import strftime
import os

class CommitChecker:
    """
    Class to check if there are any uncommitted changes and return last commit message
    The main script must be run from the root of the project

    # Arguments
        target_extensions: List of extensions to check for. Default: [".py"]
        debug_mode: If True, will not check for uncommitted changes and will return empty commit and commit message
    """
    def __init__(self, target_extensions:Optional[List[str]]=None,debug_mode: bool=False):
        self.debug_mode = debug_mode
        if target_extensions is None:
            self.target_extensions = [".py"]
        else:
            self.target_extensions = target_extensions

        commit,commit_message = self.check()
        runs_dir = Path(".").joinpath("runs")
        self.log_dir = runs_dir.joinpath(f"{strftime('%Y%m%d-%Hh%Mmin%Ss')}_{commit}")
        if not os.path.exists(str(runs_dir)):
            print(f"WARNING: runs directory does not exist. Creating it at {runs_dir.resolve()}")
            os.mkdir(str(runs_dir))
        # Add commit hash to the tr,valid logs
        for folder in ["train", "validation"]:
            file_writer = tf.summary.create_file_writer(str(self.log_dir.joinpath(folder)))
            with file_writer.as_default():
                tf.summary.text("Description commit", commit_message, step=0)
                file_writer.flush()
    def check(self):
        """Check if there are any uncommitted changes and return last commit and associated commmit message"""
        commit = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD']).decode("utf-8").strip()
        commit_message = subprocess.check_output(
            ['git', 'log', '--oneline']).decode("utf-8").strip().split("\n")[0]
        changes = subprocess.check_output(
            ['git', 'diff', '--name-only', "--", *self.target_extensions]).decode("ascii").split("\n")[:-1]
        if len(changes) and not self.debug_mode:
            changes_str = "\n".join(list(map(lambda x: '\t- ' + x, changes)))
            input(
                f"There are {len(changes)} uncommitted python files:\n{changes_str}\n Are you sure you want to continue ?")
        return commit,commit_message