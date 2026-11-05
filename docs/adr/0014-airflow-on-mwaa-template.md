# 0014: Airflow DAG and MWAA setup in the Snowflake template

This record explains how the Snowflake template loads data and runs dbt on Amazon MWAA. Read it before changing `templates/snowflake-airflow/airflow/`.

**Status:** Accepted (implemented on the 2.0 branch; not yet run on a live MWAA environment). Date: 2026-10-31.

## Context

[0004](0004-airflow-on-mwaa.md) makes Airflow on MWAA the default orchestrator, and [0006](0006-native-loaders-and-dbt-tests.md) says generated projects load with the warehouse's own loader and test with dbt, without quicketl at runtime.

MWAA supports Airflow 3.3.1 on Python 3.12 and requires every package to fit the Airflow constraints file. dbt's dependencies often clash with Airflow's. AWS's own MWAA dbt sample installs dbt in a separate virtual environment from a startup script.

## Decision

- **Airflow 3.3.1** (chosen by the user on 2026-10-31). DAGs use the Airflow 3 imports: `airflow.sdk` for `dag` and `task`, `airflow.providers.standard.operators.bash` for `BashOperator`.
- **dbt in its own virtual environment** (chosen by the user), created on workers by `startup.sh`, run with a `BashOperator`. Not Astronomer Cosmos: fewer moving parts for the first version.
- **One DAG:** a mapped `load_source` task per source, then `dbt_build`.
- **Loading with native Snowflake SQL:** file format and stage on the storage integration, a table inferred from the files on the first run (`INFER_SCHEMA` with `USING TEMPLATE`), then `COPY INTO ... MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE`. The table-exists check is done in Python because `CREATE TABLE IF NOT EXISTS ... USING TEMPLATE` is not documented.
- **Two Airflow connections,** `snowflake_loader` and `snowflake_dbt`, so loading and transforming run as different users and roles.
- **The Airflow Variable `platform_environment`** picks the environment, so the same files serve every MWAA environment.
- **Pins come from the Airflow 3.3.1 constraints file:** `apache-airflow-providers-snowflake==6.16.0` and `apache-airflow-providers-standard==1.17.0`.

## Consequences

Positive:

- The load is idempotent: Snowflake's load metadata skips files already loaded.
- dbt upgrades do not touch Airflow's dependencies.
- The check script installs the generated `requirements.txt` and imports the DAGs with Airflow's own `DagBag`, so import errors are caught before deploy.

Negative:

- `startup.sh` follows the AWS sample, including `chmod -R 777` on the virtual environment so the worker user can install into it.
- Inferred tables take their columns from the first files. Later schema changes need a manual `ALTER TABLE` or a reload.
- CSV files need a header row.
- dbt reads its private key from the `snowflake_dbt` connection's `private_key_content` as PEM text; this has not been tested against a live account.
- Nothing here has run on MWAA yet: the startup script, the S3 layout and the connections are checked only by reading the AWS docs.
