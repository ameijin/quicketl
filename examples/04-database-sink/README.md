# Example: Database Sink

Demonstrates writing pipeline output to a database. The included pipeline.yml
writes to a local Parquet file by default. See the comments in the YAML for
how to switch to a real database connection with upsert mode.

## Database Modes

- `append` - Add rows to existing table
- `truncate` - Clear table then insert
- `replace` - Drop and recreate table
- `upsert` - Update matching rows, insert new ones

## Run

```bash
cd examples/04-database-sink
quicketl run pipeline.yml
```
