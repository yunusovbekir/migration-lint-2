# Migration Lint

`migration-lint` is a modular linter tool designed to perform checks on database schema migrations and prevent unsafe operations.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Loaders](#loaders)
- [Extractors](#extractors)
- [Rules](#rules)
- [Migration Classification](#migration-classification)
- [Documentation](#documentation)
- [Feedback](#feedback)

---

## Features

- Works with [Django migrations](https://docs.djangoproject.com/en/5.1/topics/migrations/), [Alembic](https://alembic.sqlalchemy.org/en/latest/), and raw SQL files.
- Easily extensible for other frameworks.
- Identifies **Backward Incompatible** operations and checks if they are allowed in the current context.
- Detects **unsafe** operations (e.g. those that acquire locks dangerous for production databases).
- Supports declarative rules definition for custom linting logic.

---

## Installation

```shell
poetry add "migration-lint"
```

```shell
pip install "migration-lint"
```

---

## Quick Start

```shell
migration-lint --loader=local_git --extractor=django
```

Run this in your project root to lint uncommitted migration changes using the local git loader.

---

## Loaders

Loaders determine where `migration-lint` picks up the list of changed migration files.

| Loader | Use case |
|---|---|
| `local_git` | Uncommitted local changes (e.g. pre-commit hook) |
| `gitlab_branch` | GitLab CI — branch comparison |
| `gitlab_mr` | GitLab CI — Merge Request comparison |

See the full [loader documentation](docs/index.md#loaders) for configuration options and examples.

---

## Extractors

Extractors translate migration files into SQL for analysis.

| Extractor | Framework |
|---|---|
| `django` | Django migrations |
| `alembic` | Alembic (SQLAlchemy) |
| `flyway` | Flyway raw SQL |
| `raw_sql` | Plain SQL files |

See the full [extractor documentation](docs/index.md#extractors) for setup guides and CI examples.

---

## Rules

`migration-lint` uses a declarative rules API to define what SQL operations are allowed, restricted, or require special handling. Rules are evaluated in order from safest to most dangerous:

1. Ignored
2. Data migration
3. Backward compatible
4. Backward incompatible
5. Restricted

See the [Rules documentation](docs/rules.md) for the full API reference and examples.

To ignore a specific migration:

```sql
-- migration-lint: ignore
```

---

## Migration Classification

Migrations are classified into stages based on safety:

| Stage | Description | Auto-run |
|---|---|---|
| `stage1` | Backward-compatible schema migration | ✅ Safe |
| `stage2` | Data backfill migration | ⚠️ Not safe on prod |
| `stage3` | Code prep for backward-incompatible change | — |
| `stage4` | Backward-incompatible schema migration | ❌ No on prod |

See the [Classification documentation](docs/classification.md) for detailed patterns covering indexes, tables, columns, constraints, and more.

---

## Documentation

| Document | Description |
|---|---|
| [Overview & Getting Started](docs/index.md) | Installation, loaders, extractors, and terminology |
| [Migration Classification](docs/classification.md) | Safe vs. unsafe migration patterns with SQL examples |
| [Rules API](docs/rules.md) | How to define and use linting rules |
| [Tags](docs/tags.md) | Tag reference |
