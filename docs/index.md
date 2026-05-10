# Welcome to **migration-lint**

`migration-lint` is the modular linter tool designed
to perform checks on database schema migrations
and prevent unsafe operations.

Features:

- Works with [Django migrations](https://docs.djangoproject.com/en/5.1/topics/migrations/),
  [Alembic](https://alembic.sqlalchemy.org/en/latest/) and raw sql files.
- Easily extensible for other frameworks.
- Can identify Backward Incompatible operations
  and check if they are allowed in the current context.
- Can identify "unsafe" operations, e.g. operations that acquire locks
  that can be dangerous for production database.

## Installation

```shell linenums="0"
poetry add "migration-lint"
```

```shell linenums="0"
pip install "migration-lint"
```

## Terms

- **Source loader** (or just loader) - class that loads list of changed files.
- **Extractor** - class that extracts SQL by migration name,
  so it depends on the framework you use for migrations.
- **Linter** - class that checks migration's SQL and context
  and returns errors if any. We have implemented our linter
  for backward incompatible migrations as well as integrated `squawk` linter.

---

## Loaders

Loaders determine where `migration-lint` picks up the list of changed migration files.

### Local git

Use this when you want to check uncommitted changes locally (e.g. in a pre-commit hook):

```shell linenums="0"
migration-lint --loader=local_git --extractor=<extractor>
```

It will examine files in the current repository that are added or modified and not yet committed.

### GitLab

Use this when running inside a GitLab CI pipeline:

```shell linenums="0"
migration-lint --loader=gitlab_branch --extractor=<extractor>
```

It relies on default GitLab [environment variables](https://docs.gitlab.com/ee/ci/variables/predefined_variables.html):
`CI_SERVER_URL`, `CI_PROJECT_ID`, `CI_MERGE_REQUEST_SOURCE_BRANCH_NAME`
(falls back to `CI_COMMIT_BRANCH`).
You also need to issue a token with read permissions and put it into `CI_DEPLOY_GITLAB_TOKEN`.
If `CI_SERVER_URL` is not available (for example, outside GitLab CI), pass `--gitlab-instance` explicitly.

Parameters can also be passed explicitly:

```shell linenums="0"
migration-lint --loader=gitlab_branch --extractor=<extractor> \
  --gitlab-instance=<url> --project-id=<proj id> --branch=<branch> --gitlab-api-key=<key>
```

### GitLab MR

A Merge Request variant is also available. It compares the files changed in the MR directly.
It uses `CI_MERGE_REQUEST_ID`, `CI_PROJECT_ID` and `CI_DEPLOY_GITLAB_TOKEN` from the environment:

```shell linenums="0"
migration-lint --loader=gitlab_mr --extractor=<extractor>
```

Or pass values explicitly:

```shell linenums="0"
migration-lint --loader=gitlab_mr --extractor=<extractor> \
  --project-id=<proj id> --mr-id=<mr id> --gitlab-api-key=<key>
```

---

## Extractors

Extractors know how to turn migration files into SQL for a given framework.
Pick the one that matches your project.

### Alembic

#### Prerequisites

- Your project uses [Alembic](https://alembic.sqlalchemy.org/en/latest/) for database migrations.
- Alembic can run in **offline mode** and produce SQL output (e.g. `alembic upgrade head --sql`).

#### Configure the SQL command

`migration-lint` runs Alembic in offline mode and captures its SQL output.
By default it calls:

```shell linenums="0"
make sqlmigrate
```

Override this with the `--alembic-command` flag or the `MIGRATION_LINTER_ALEMBIC_COMMAND` environment variable:

```shell linenums="0"
migration-lint --extractor=alembic \
  --alembic-command="alembic upgrade head --sql"
```

```shell linenums="0"
export MIGRATION_LINTER_ALEMBIC_COMMAND="alembic upgrade head --sql"
```

Make sure the command prints the full SQL to **stdout**, including the
`-- Running upgrade ... -> <revision>` comment lines that Alembic emits.

#### Set the migrations path

`migration-lint` identifies Alembic migration files by checking whether their path
contains the configured migrations directory. The default is:

```
/migrations/versions/
```

Override it with an environment variable:

```shell linenums="0"
export MIGRATION_LINT_ALEMBIC_MIGRATIONS_PATH="/app/alembic/versions/"
```

#### Handle extraction errors (optional)

| Flag | Description |
|---|---|
| `--ignore-extractor-fail` | If the SQL command fails, log an error and continue instead of raising. |
| `--ignore-extractor-not-found` | If a revision is missing from the SQL output, log an error and skip it. |

#### Full GitLab CI example

```yaml
migration-lint:
  stage: lint
  image: python:3.12-slim
  variables:
    MIGRATION_LINT_ALEMBIC_MIGRATIONS_PATH: "/app/alembic/versions/"
  script:
    - pip install migration-lint
    - migration-lint --loader=gitlab_branch --extractor=alembic --alembic-command="alembic upgrade head --sql"
```

#### How it works

1. The configured **loader** collects the list of changed files.
2. Each file living under `MIGRATION_LINT_ALEMBIC_MIGRATIONS_PATH` and ending with `.py` is treated as a migration.
   Its **revision ID** is parsed from the filename — specifically the second segment when the name is split by `_`.
   For example, a file named `0001_abc123_add_users_table.py` would yield the revision ID `abc123`.
   Make sure your migration filenames follow the `<index>_<revision>_<description>.py` pattern.
3. The configured **alembic command** is run once and its output is cached.
4. Each revision is matched to its SQL block, delimited by `-- Running upgrade ... -> <revision>` lines.
5. The extracted SQL is passed to the **linter** for analysis.

---
