import os
from typing import Sequence

from migration_lint import logger
from migration_lint.source_loader.base import BaseSourceLoader
from migration_lint.source_loader.model import SourceDiff


class LocalLoader(BaseSourceLoader):
    """A loader to obtain files changed for local stashed files."""

    NAME = "local_git"

    def get_changed_files(self) -> Sequence[SourceDiff]:
        """Return a list of changed files."""

        from git import BadName, Repo

        logger.info("### Getting changed files for local stashed files")

        repo = Repo(os.getcwd(), search_parent_directories=True)

        # Diffs between HEAD and the working tree (uncommitted changes).
        diffs = list(repo.head.commit.diff(None))

        # Also include files that were stashed with `git stash`.  The stash is
        # stored as a commit on refs/stash whose first parent is the HEAD that
        # was current at stash time.  Diffing that parent against the stash
        # commit yields exactly the set of changes that were stashed.
        try:
            stash_commit = repo.commit("refs/stash")
            stash_base = stash_commit.parents[0]
            existing_paths = {d.b_path for d in diffs}
            for d in stash_base.diff(stash_commit):
                if d.b_path not in existing_paths:
                    diffs.append(d)
        except (BadName, IndexError):
            pass  # No stash exists or stash has unexpected structure.

        filtered_diffs = [
            d
            for d in diffs
            if not d.deleted_file
            and (not self.only_new_files or self.only_new_files and d.new_file)
        ]

        logger.info("Files changed: ")
        logger.info("\n".join([f"- {d.a_path}" for d in filtered_diffs]))

        return [
            SourceDiff(old_path=diff.a_path, path=diff.b_path)
            for diff in filtered_diffs
        ]
