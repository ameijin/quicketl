# Example: Workflow (Medallion Architecture)

Demonstrates a multi-stage workflow with parallel pipeline execution following
the bronze -> silver -> gold medallion pattern.

The silver stage runs two pipelines in parallel (clean_sales, clean_regions),
then the gold stage aggregates the cleaned data.

## Run

```bash
cd examples/05-workflow
quicketl workflow run workflow.yml
```
