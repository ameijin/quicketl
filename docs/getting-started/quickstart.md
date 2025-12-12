# Quick Start

Get up and running with ETLX in 5 minutes.

## Create a New Project

Use the `etlx init` command to create a new project with sample data:

```bash
quicketl init my_project
cd my_project
```

This creates:

```
my_project/
├── pipelines/
│   └── sample.yml      # Sample pipeline configuration
├── data/
│   └── sales.csv       # Sample data to process
├── README.md           # Project documentation
├── .env                # Environment variables
└── .gitignore
```

## Run the Sample Pipeline

Run the included sample pipeline:

```bash
quicketl run pipelines/sample.yml
```

You'll see output like:

```
Running pipeline: sample_pipeline
  Sample ETL pipeline - processes sales data
  Engine: duckdb

╭───────────────────────── Pipeline: sample_pipeline ──────────────────────────╮
│ SUCCESS                                                                      │
╰───────────────────────────── Duration: 245.3ms ──────────────────────────────╯
                              Steps
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓
┃ Step                      ┃ Type          ┃ Status ┃ Duration ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━┩
│ read_source               │ file          │ OK     │   45.2ms │
│ transform_0_filter        │ filter        │ OK     │    0.3ms │
│ transform_1_derive_column │ derive_column │ OK     │    0.2ms │
│ transform_2_aggregate     │ aggregate     │ OK     │    0.8ms │
│ transform_3_sort          │ sort          │ OK     │    0.1ms │
│ quality_checks            │ checks        │ OK     │   12.4ms │
│ write_sink                │ file          │ OK     │    8.1ms │
└───────────────────────────┴───────────────┴────────┴──────────┘

Quality Checks: PASSED (2/2 passed)

Rows processed: 3
Rows written: 3
```

## Examine the Output

The pipeline created a Parquet file in `data/output/`:

```bash
ls data/output/
# sales_summary.parquet
```

## Understand the Pipeline

Open `pipelines/sample.yml` to see the configuration:

```yaml title="pipelines/sample.yml"
name: sample_pipeline
description: Sample ETL pipeline - processes sales data
engine: duckdb

source:
  type: file
  path: data/sales.csv
  format: csv

transforms:
  - op: filter
    predicate: amount > 0

  - op: derive_column
    name: total_with_tax
    expr: amount * 1.1

  - op: aggregate
    group_by: [category]
    aggs:
      total_sales: sum(amount)
      total_with_tax: sum(total_with_tax)
      order_count: count(*)

  - op: sort
    by: [total_sales]
    descending: true

checks:
  - type: not_null
    columns: [category, total_sales]
  - type: row_count
    min: 1

sink:
  type: file
  path: data/output/sales_summary.parquet
  format: parquet
```

### Key Sections

| Section | Description |
|---------|-------------|
| `name` | Pipeline identifier |
| `engine` | Compute backend (duckdb, polars, spark) |
| `source` | Where to read data from |
| `transforms` | List of data transformations |
| `checks` | Data quality validations |
| `sink` | Where to write output |

## Modify the Pipeline

Try changing the pipeline:

1. **Change the aggregation grouping:**

    ```yaml
    - op: aggregate
      group_by: [category, region]  # Add region
      aggs:
        total_sales: sum(amount)
    ```

2. **Add a new filter:**

    ```yaml
    - op: filter
      predicate: category = 'Electronics'
    ```

3. **Run again:**

    ```bash
    quicketl run pipelines/sample.yml
    ```

## Use Variables

Pass variables at runtime:

```yaml title="pipelines/sample.yml"
source:
  type: file
  path: data/${DATE}/sales.csv  # Use variable
  format: csv
```

```bash
quicketl run pipelines/sample.yml --var DATE=2025-01-15
```

## Validate Without Running

Check your configuration is valid without executing:

```bash
quicketl validate pipelines/sample.yml
```

## Dry Run

Execute transforms without writing output:

```bash
quicketl run pipelines/sample.yml --dry-run
```

## What's Next?

<div class="grid cards" markdown>

-   :material-school:{ .lg .middle } **Your First Pipeline**

    ---

    Build a pipeline from scratch with detailed explanations.

    [:octicons-arrow-right-24: First Pipeline](first-pipeline.md)

-   :material-cog:{ .lg .middle } **Configuration Guide**

    ---

    Learn all the configuration options.

    [:octicons-arrow-right-24: Configuration](../user-guide/configuration/index.md)

-   :material-swap-horizontal:{ .lg .middle } **Transforms**

    ---

    Explore all 12 transform operations.

    [:octicons-arrow-right-24: Transforms](../user-guide/transforms/index.md)

</div>
