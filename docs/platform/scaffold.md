# Scaffold and Update a Platform

`quicketl platform scaffold` turns a [platform spec](spec.md) into a project folder. `quicketl platform update` applies later spec or template changes to that folder. Use them when you start a new platform and whenever the spec changes.

!!! note "What the template generates today"
    The Snowflake and Airflow template currently writes the Snowflake Terraform, a `README.md` describing the platform, a `.gitignore` and `.copier-answers.yml`. See [Snowflake and Airflow Template](snowflake-airflow.md). dbt and Airflow code arrive in later template versions, and `quicketl platform update` will pick them up.

## Before you start

- Install quicketl (`pip install quicketl`). Scaffolding is part of the core install.
- Install `git`. quicketl uses it to fetch templates.
- Write and check a spec: `quicketl platform init`, edit `platform.yml`, then `quicketl platform validate`.

Only `snowflake` with `airflow` has a template so far. A spec for `databricks` or `redshift_serverless` validates but cannot be scaffolded yet.

## Generate a project

From the folder that holds `platform.yml`:

```bash
quicketl platform scaffold
```

quicketl validates the spec, picks the template for its warehouse and orchestrator, and renders it into the same folder. Then put the project in git:

```bash
git init
git add -A
git commit -m "Scaffold platform"
```

To generate somewhere else, pass `--dest`. quicketl copies `platform.yml` there too, so the project carries its own spec:

```bash
quicketl platform scaffold platform.yml --dest ../acme-platform
```

## Change the platform later

1. Edit `platform.yml` in the project.
2. Run `quicketl platform validate`.
3. Commit everything. Update refuses to run on uncommitted changes.
4. Run:

    ```bash
    quicketl platform update
    ```

5. Review the changes with `git diff`. Where a template change clashes with your own edits, the file has conflict markers (`<<<<<<<` and `>>>>>>>`) for you to resolve.

## Which template version is used

Templates live in the quicketl repo and are versioned by its release tags. By default, both commands use the tag that matches your installed quicketl, for example `v2.0.0`. So upgrading quicketl and running `quicketl platform update` moves the project to the matching template.

Pick a version yourself with `--ref`:

```bash
quicketl platform update --ref v2.1.0
```

The tag used is recorded in `.copier-answers.yml` as `_commit`. Do not edit that file by hand.

## Options

| Command | Option | What it does |
|---------|--------|--------------|
| `scaffold` | `[spec_file]` | Spec to use. Default: `platform.yml`. |
| `scaffold` | `--dest`, `-d` | Folder to generate into. Default: the spec's folder. |
| `scaffold` | `--ref`, `-r` | Template tag. Default: `v<installed quicketl version>`. |
| `scaffold` | `--template`, `-t` | Template repo URL or local path. Default: the quicketl repo on GitHub. Use a local path when developing templates. |
| `update` | `[project]` | Generated project folder. Default: the current folder. |
| `update` | `--ref`, `-r` | Template tag. Default: `v<installed quicketl version>`. |

## When something goes wrong

| Message | What to do |
|---------|------------|
| `No template yet for databricks-airflow` | Only `snowflake-airflow` exists today. |
| `... was already generated (it has .copier-answers.yml)` | Use `quicketl platform update` instead. |
| `Unknown revision: 'v9.9.9'` | The `--ref` tag does not exist in the template repo. |
| `Destination repository is dirty` | Commit or stash your changes, then run update again. |
| `Updating is only supported in git-tracked subprojects` | Put the project in git and commit it first. |
| `... has no .copier-answers.yml` | The folder was not made by `scaffold`. Run `scaffold` first. |

How this works, and why, is recorded in [ADR 0011](../adr/0011-copier-template-layout.md).
