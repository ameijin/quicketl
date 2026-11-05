# Backend Support Matrix

This page lists every backend quicketl knows about, how to install it, and whether the project's tests exercise it. Use it to decide how much to trust a backend before you build on it.

The list comes from the backend registry in `src/quicketl/engines/backends.py`. It has 12 backends.

## Status meanings

| Status | Meaning |
|--------|---------|
| Tested in CI | The automated test suite runs quicketl pipelines or transforms on this backend. |
| Available, untested | The backend is registered and you can select it, but no automated test runs on it. It may work. Report problems. |
| Not supported (planned) | There is no code for this backend yet. |

## Matrix

| Backend | Install extra | Status |
|---------|---------------|--------|
| DuckDB | `quicketl[pipelines]` | Tested in CI |
| Polars | `quicketl[pipelines]` | Tested in CI |
| DataFusion | `quicketl[datafusion]` | Available, untested |
| pandas | `quicketl[pandas]` | Available, untested |
| Apache Spark | `quicketl[spark]` | Available, untested |
| Google BigQuery | `quicketl[bigquery]` | Available, untested |
| Snowflake | `quicketl[snowflake]` | Available, untested |
| Trino | `quicketl[trino]` | Available, untested |
| PostgreSQL | `quicketl[postgres]` | Available, untested |
| MySQL | `quicketl[mysql]` | Available, untested |
| ClickHouse | `quicketl[clickhouse]` | Available, untested |
| SQLite | None (no extra is defined) | Available, untested |
| Databricks | Not applicable | Not supported (planned) |
| Redshift | Not applicable | Not supported (planned) |

## How "Tested in CI" is decided

- The shared test fixtures in `tests/conftest.py` run each engine test on `duckdb` and `polars`.
- The parity tests in `tests/parity/` compare DuckDB and Polars results. Their backend list is `PARITY_BACKENDS = ["duckdb", "polars"]`.
- Some database-sink tests write to SQLite files, and some integration tests need a PostgreSQL or MySQL server. Those tests use the database as a write target. They do not run the pipeline engine on it. The server tests are skipped unless you set `QUICKETL_TEST_POSTGRES_URI` or `QUICKETL_TEST_MYSQL_URI`. For that reason these three backends are listed as untested.
- No test selects `datafusion`, `bigquery`, `trino` or `clickhouse`. The Snowflake tests only check configuration loading. The Spark test only checks that the engine name is passed through to a mocked task.

## Related pages

- [Backends overview](index.md)
- [Local backends](local.md)
- [Distributed (Spark)](distributed.md)
- [Cloud warehouses](cloud-warehouses.md)
- [Databases](databases.md)
