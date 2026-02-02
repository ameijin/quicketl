"""Tests for retry logic with exponential backoff."""

from __future__ import annotations

from unittest import mock

import pytest

from quicketl.io.retry import (
    DEFAULT_BASE_DELAY,
    DEFAULT_MAX_RETRIES,
    is_cloud_path,
    with_retry,
)


class TestIsCloudPath:
    """Tests for cloud path detection."""

    @pytest.mark.parametrize(
        "path",
        [
            "s3://bucket/data.parquet",
            "gs://bucket/data.csv",
            "gcs://bucket/data.json",
            "az://container/data.parquet",
            "abfss://container@account.dfs.core.windows.net/data",
            "abfs://container/data",
        ],
    )
    def test_cloud_paths_detected(self, path: str):
        assert is_cloud_path(path) is True

    @pytest.mark.parametrize(
        "path",
        [
            "/local/data.parquet",
            "./relative/data.csv",
            "data.json",
            "file:///local/data.parquet",
            "http://example.com/data.csv",
        ],
    )
    def test_local_paths_not_detected(self, path: str):
        assert is_cloud_path(path) is False


class TestWithRetry:
    """Tests for retry with exponential backoff."""

    def test_succeeds_on_first_try(self):
        fn = mock.Mock(return_value="ok")
        result = with_retry(fn)
        assert result == "ok"
        assert fn.call_count == 1

    def test_retries_on_transient_error(self):
        fn = mock.Mock(side_effect=[OSError("timeout"), "ok"])
        with mock.patch("quicketl.io.retry.time.sleep"):
            result = with_retry(fn, max_retries=2)
        assert result == "ok"
        assert fn.call_count == 2

    def test_exhausts_retries_then_raises(self):
        fn = mock.Mock(side_effect=OSError("persistent failure"))
        with mock.patch("quicketl.io.retry.time.sleep"), pytest.raises(OSError, match="persistent failure"):
            with_retry(fn, max_retries=2)
        # initial attempt + 2 retries = 3 calls
        assert fn.call_count == 3

    def test_non_retryable_error_propagates_immediately(self):
        fn = mock.Mock(side_effect=ValueError("bad input"))
        with pytest.raises(ValueError, match="bad input"):
            with_retry(fn, max_retries=3)
        assert fn.call_count == 1

    def test_exponential_backoff_delays(self):
        fn = mock.Mock(side_effect=[OSError("1"), OSError("2"), "ok"])
        with mock.patch("quicketl.io.retry.time.sleep") as mock_sleep:
            with_retry(fn, max_retries=3, base_delay=1.0)
        # First retry: 1.0 * 2^0 = 1.0s
        # Second retry: 1.0 * 2^1 = 2.0s
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1.0)
        mock_sleep.assert_any_call(2.0)

    def test_max_delay_caps_backoff(self):
        fn = mock.Mock(
            side_effect=[OSError("1"), OSError("2"), OSError("3"), "ok"]
        )
        with mock.patch("quicketl.io.retry.time.sleep") as mock_sleep:
            with_retry(fn, max_retries=4, base_delay=10.0, max_delay=15.0)
        # Delays: min(10*2^0,15)=10, min(10*2^1,15)=15, min(10*2^2,15)=15
        assert mock_sleep.call_args_list == [
            mock.call(10.0),
            mock.call(15.0),
            mock.call(15.0),
        ]

    def test_passes_args_and_kwargs(self):
        fn = mock.Mock(return_value="result")
        result = with_retry(fn, "a", "b", key="val")
        fn.assert_called_once_with("a", "b", key="val")
        assert result == "result"

    def test_custom_retryable_exceptions(self):
        fn = mock.Mock(side_effect=[RuntimeError("transient"), "ok"])
        with mock.patch("quicketl.io.retry.time.sleep"):
            result = with_retry(
                fn,
                max_retries=2,
                retryable_exceptions=(RuntimeError,),
            )
        assert result == "ok"

    def test_default_settings(self):
        assert DEFAULT_MAX_RETRIES == 3
        assert DEFAULT_BASE_DELAY == 1.0
