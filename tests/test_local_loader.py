from __future__ import annotations

from unittest import mock

from git import BadName

from migration_lint.source_loader.local import LocalLoader


def _make_diff(a_path, b_path, deleted_file=False, new_file=False):
    d = mock.MagicMock()
    d.a_path = a_path
    d.b_path = b_path
    d.deleted_file = deleted_file
    d.new_file = new_file
    return d


def test_local_loader_working_tree_changes():
    """Files with uncommitted changes (not stashed) are detected."""
    loader = LocalLoader(only_new_files=False)

    diff_a = _make_diff("a.py", "a.py", new_file=True)
    diff_b = _make_diff("b.py", "b.py")

    repo_mock = mock.MagicMock()
    repo_mock.head.commit.diff.return_value = [diff_a, diff_b]
    # Simulate no stash.
    repo_mock.commit.side_effect = BadName("refs/stash")

    with mock.patch("git.Repo", return_value=repo_mock):
        result = loader.get_changed_files()

    assert len(result) == 2
    assert result[0].path == "a.py"
    assert result[1].path == "b.py"


def test_local_loader_stash_changes():
    """Files that are stashed (refs/stash) are detected."""
    loader = LocalLoader(only_new_files=False)

    # No working-tree diffs.
    repo_mock = mock.MagicMock()
    repo_mock.head.commit.diff.return_value = []

    # Stash commit whose parent diff contains a new migration file.
    stash_diff = _make_diff("migration.py", "migration.py", new_file=True)
    stash_parent = mock.MagicMock()
    stash_parent.diff.return_value = [stash_diff]

    stash_commit = mock.MagicMock()
    stash_commit.parents = [stash_parent]

    repo_mock.commit.return_value = stash_commit

    with mock.patch("git.Repo", return_value=repo_mock):
        result = loader.get_changed_files()

    assert len(result) == 1
    assert result[0].path == "migration.py"


def test_local_loader_no_duplicate_when_stash_overlaps_working_tree():
    """Files present in both working tree and stash are not duplicated."""
    loader = LocalLoader(only_new_files=False)

    diff_wt = _make_diff("shared.py", "shared.py", new_file=True)
    repo_mock = mock.MagicMock()
    repo_mock.head.commit.diff.return_value = [diff_wt]

    # Stash contains the same file.
    stash_diff = _make_diff("shared.py", "shared.py", new_file=True)
    stash_parent = mock.MagicMock()
    stash_parent.diff.return_value = [stash_diff]
    stash_commit = mock.MagicMock()
    stash_commit.parents = [stash_parent]
    repo_mock.commit.return_value = stash_commit

    with mock.patch("git.Repo", return_value=repo_mock):
        result = loader.get_changed_files()

    assert len(result) == 1
    assert result[0].path == "shared.py"


def test_local_loader_only_new_files_filters_stash():
    """only_new_files=True skips modified (non-new) files from the stash."""
    loader = LocalLoader(only_new_files=True)

    repo_mock = mock.MagicMock()
    repo_mock.head.commit.diff.return_value = []

    new_file_diff = _make_diff("new.py", "new.py", new_file=True)
    modified_diff = _make_diff("old.py", "old.py", new_file=False)

    stash_parent = mock.MagicMock()
    stash_parent.diff.return_value = [new_file_diff, modified_diff]
    stash_commit = mock.MagicMock()
    stash_commit.parents = [stash_parent]
    repo_mock.commit.return_value = stash_commit

    with mock.patch("git.Repo", return_value=repo_mock):
        result = loader.get_changed_files()

    assert len(result) == 1
    assert result[0].path == "new.py"


def test_local_loader_deleted_files_excluded_from_stash():
    """Deleted files in the stash are always excluded."""
    loader = LocalLoader(only_new_files=False)

    repo_mock = mock.MagicMock()
    repo_mock.head.commit.diff.return_value = []

    deleted_diff = _make_diff("gone.py", "gone.py", deleted_file=True)
    stash_parent = mock.MagicMock()
    stash_parent.diff.return_value = [deleted_diff]
    stash_commit = mock.MagicMock()
    stash_commit.parents = [stash_parent]
    repo_mock.commit.return_value = stash_commit

    with mock.patch("git.Repo", return_value=repo_mock):
        result = loader.get_changed_files()

    assert len(result) == 0
