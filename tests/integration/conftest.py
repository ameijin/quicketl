"""Integration test fixtures and configuration.

Integration tests run against real databases and external services.
They are slower but test actual end-to-end behavior.
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session")
def postgres_connection_string():
    """Get PostgreSQL connection string from environment or skip.

    Set QUICKETL_TEST_POSTGRES_URI to run integration tests:
    export QUICKETL_TEST_POSTGRES_URI="postgresql://user:pass@localhost:5432/testdb"
    """
    uri = os.environ.get("QUICKETL_TEST_POSTGRES_URI")
    if not uri:
        pytest.skip("PostgreSQL connection not configured (set QUICKETL_TEST_POSTGRES_URI)")
    return uri


@pytest.fixture(scope="session")
def mysql_connection_string():
    """Get MySQL connection string from environment or skip.

    Set QUICKETL_TEST_MYSQL_URI to run integration tests:
    export QUICKETL_TEST_MYSQL_URI="mysql://user:pass@localhost:3306/testdb"
    """
    uri = os.environ.get("QUICKETL_TEST_MYSQL_URI")
    if not uri:
        pytest.skip("MySQL connection not configured (set QUICKETL_TEST_MYSQL_URI)")
    return uri


@pytest.fixture(scope="session")
def s3_test_bucket():
    """Get S3 test bucket from environment or skip.

    Set QUICKETL_TEST_S3_BUCKET to run S3 integration tests:
    export QUICKETL_TEST_S3_BUCKET="s3://my-test-bucket/quicketl-tests/"

    Also ensure AWS credentials are configured.
    """
    bucket = os.environ.get("QUICKETL_TEST_S3_BUCKET")
    if not bucket:
        pytest.skip("S3 bucket not configured (set QUICKETL_TEST_S3_BUCKET)")
    return bucket
