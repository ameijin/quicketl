# How Relative Paths Are Resolved

This page explains where QuickETL looks for files when a pipeline uses a relative path such as `data/sales.csv`. Read it if a pipeline works from one folder and fails from another.

## Example

Put a `quicketl.yml` file in the root of your project:

```
my_project/
├── quicketl.yml            # Marks the project root
├── pipelines/
│   └── sales.yml
└── data/
    ├── sales.csv
    └── output/
```

The pipeline uses paths relative to the project root:

```yaml title="pipelines/sales.yml"
name: sales
source:
  type: file
  path: data/sales.csv
  format: csv
sink:
  type: file
  path: data/output/sales.parquet
  format: parquet
```

Run it from any folder. The paths still point into `my_project/`:

```bash
cd /tmp
quicketl run /path/to/my_project/pipelines/sales.yml
```

## The Rule

For each file source and file sink, QuickETL turns a relative `path` into an absolute one. It picks the base folder in this order:

1. The `--base-dir` option (or the `base_dir` argument in Python), if you give one.
2. The folder of the nearest `quicketl.yml` (or `quicketl.yaml`). QuickETL searches up from the folder that holds the pipeline file.
3. Otherwise, nothing changes. Paths resolve against the current working directory.

This applies to `source`, to every entry under `sources`, and to `sink`.

## Set the Base Folder for a Scheduler

Schedulers such as Airflow often start jobs from a folder you do not control. Pass `--base-dir` to pin the data folder:

```bash
quicketl run /opt/project/pipelines/sales.yml --base-dir /opt/project
quicketl workflow run /opt/project/workflows/etl.yml --base-dir /opt/project
```

In Python, use the `base_dir` argument:

```python
from quicketl import Pipeline

pipeline = Pipeline.from_yaml(
    "/opt/project/pipelines/sales.yml",
    base_dir="/opt/project",
)
```

`Workflow.from_yaml` takes the same `base_dir` argument.

In a workflow, the `path:` of each stage still resolves against the folder of the workflow file. `--base-dir` only changes the data paths inside each pipeline.

## What Is Never Changed

QuickETL leaves these values as they are:

- Absolute paths, such as `/data/sales.csv`.
- Remote locations that contain `://`, such as `s3://`, `gs://`, and `az://`.
- Database connection strings. A relative SQLite path still resolves against the current working directory.

The file sink does not create missing folders. Create the output folder (for example `data/output/`) before you run the pipeline.

## Upgrading from 1.6

Nothing changes unless you add a `quicketl.yml`. Without one, paths resolve against the current working directory, as in 1.6.

`quicketl init` now creates a `quicketl.yml`. In an existing folder, it never overwrites one that is already there.

## See Also

- [Project Structure](../../getting-started/project-structure.md)
- [Pipeline YAML Reference](pipeline-yaml.md)
- [CLI Reference](../../reference/cli.md)
