#!/bin/bash
# MWAA startup script: installs dbt in its own virtual environment on workers,
# so dbt's dependencies never clash with Airflow's. Based on the AWS sample at
# https://docs.aws.amazon.com/mwaa/latest/userguide/samples-dbt.html
set -euo pipefail

if [[ "${MWAA_AIRFLOW_COMPONENT}" != "worker" ]]; then
  exit 0
fi

VENV_PARENT=/usr/local/airflow/python3-virtualenv
sudo mkdir -p "${VENV_PARENT}"
cd "${VENV_PARENT}"
sudo python3 -m venv dbt-env
sudo chmod -R 777 dbt-env
dbt-env/bin/pip install --quiet "dbt-core==1.12.6" "dbt-snowflake==1.12.4"
