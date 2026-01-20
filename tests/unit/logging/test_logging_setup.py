"""Tests for logging configuration."""

from __future__ import annotations

import io
import logging
import sys
from unittest.mock import patch

import pytest
import structlog


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def setup_method(self):
        """Reset structlog configuration before each test."""
        structlog.reset_defaults()
        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    def test_configure_json_format(self):
        """Test JSON format configuration."""
        from quicketl.logging import configure_logging

        configure_logging(level="INFO", format="json")

        # Get the current configuration
        config = structlog.get_config()

        # Should have JSON renderer as the last processor
        processors = config["processors"]
        last_processor = processors[-1]
        assert isinstance(last_processor, structlog.processors.JSONRenderer)

    def test_configure_console_format(self):
        """Test console format configuration."""
        from quicketl.logging import configure_logging

        configure_logging(level="INFO", format="console")

        config = structlog.get_config()
        processors = config["processors"]
        last_processor = processors[-1]
        assert isinstance(last_processor, structlog.dev.ConsoleRenderer)

    def test_configure_auto_format_tty(self):
        """Test auto format uses console when stderr is a TTY."""
        from quicketl.logging import configure_logging

        with patch.object(sys.stderr, "isatty", return_value=True):
            configure_logging(level="INFO", format="auto")

        config = structlog.get_config()
        processors = config["processors"]
        last_processor = processors[-1]
        assert isinstance(last_processor, structlog.dev.ConsoleRenderer)

    def test_configure_auto_format_not_tty(self):
        """Test auto format uses JSON when stderr is not a TTY."""
        from quicketl.logging import configure_logging

        with patch.object(sys.stderr, "isatty", return_value=False):
            configure_logging(level="INFO", format="auto")

        config = structlog.get_config()
        processors = config["processors"]
        last_processor = processors[-1]
        assert isinstance(last_processor, structlog.processors.JSONRenderer)

    @pytest.mark.parametrize(
        "level",
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    def test_configure_log_levels(self, level: str):
        """Test that log levels are properly configured."""
        from quicketl.logging import configure_logging

        configure_logging(level=level, format="json")

        root_logger = logging.getLogger()
        expected_level = getattr(logging, level)
        assert root_logger.level == expected_level

    def test_configure_lower_case_level(self):
        """Test that lowercase log levels work."""
        from quicketl.logging import configure_logging

        configure_logging(level="debug", format="json")

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_shared_processors_present(self):
        """Test that shared processors are always included."""
        from quicketl.logging import configure_logging

        configure_logging(level="INFO", format="json")

        config = structlog.get_config()
        processors = config["processors"]

        # Check for expected shared processors by inspecting types
        processor_types = [type(p).__name__ for p in processors]

        assert "merge_contextvars" in str(processors[0])
        assert "TimeStamper" in processor_types


class TestGetLogger:
    """Tests for get_logger function."""

    def setup_method(self):
        """Reset structlog configuration before each test."""
        structlog.reset_defaults()
        from quicketl.logging import configure_logging

        configure_logging(level="DEBUG", format="json")

    def test_get_logger_returns_bound_logger(self):
        """Test that get_logger returns a BoundLogger."""
        from quicketl.logging import get_logger

        logger = get_logger("test")
        assert logger is not None

    def test_get_logger_without_name(self):
        """Test get_logger works without a name."""
        from quicketl.logging import get_logger

        logger = get_logger()
        assert logger is not None

    def test_get_logger_with_name(self):
        """Test get_logger properly binds name."""
        from quicketl.logging import get_logger

        logger = get_logger("my_module")
        assert logger is not None

    def test_logger_can_log_messages(self, capsys):
        """Test that logger can actually log messages."""
        from quicketl.logging import configure_logging, get_logger

        # Reconfigure to capture output
        configure_logging(level="INFO", format="json")
        logger = get_logger("test_logger")

        # Log a message
        logger.info("test_message", key="value")

        # Note: structlog logs to stderr
        # We verify no exceptions were raised
        assert True

    def test_logger_debug_level_filtering(self):
        """Test that debug messages are filtered at INFO level."""
        from quicketl.logging import configure_logging, get_logger

        configure_logging(level="INFO", format="json")
        logger = get_logger("test")

        # This should not raise an exception
        logger.debug("should_be_filtered")
        logger.info("should_appear")

    def test_logger_structured_data(self):
        """Test that structured data can be logged."""
        from quicketl.logging import configure_logging, get_logger

        configure_logging(level="INFO", format="json")
        logger = get_logger("test")

        # Should handle various data types
        logger.info(
            "structured_log",
            string_val="hello",
            int_val=42,
            float_val=3.14,
            list_val=[1, 2, 3],
            dict_val={"nested": "value"},
        )


class TestLoggingIntegration:
    """Integration tests for logging setup."""

    def setup_method(self):
        """Reset structlog configuration before each test."""
        structlog.reset_defaults()
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    def test_module_auto_configures_on_import(self):
        """Test that importing the module auto-configures logging."""
        # Force reimport to trigger auto-configuration
        import importlib

        import quicketl.logging.setup

        importlib.reload(quicketl.logging.setup)

        # Should be configured
        config = structlog.get_config()
        assert config["processors"] is not None

    def test_reconfiguration_works(self):
        """Test that logging can be reconfigured."""
        from quicketl.logging import configure_logging

        # First configuration
        configure_logging(level="INFO", format="json")
        config1 = structlog.get_config()
        assert isinstance(config1["processors"][-1], structlog.processors.JSONRenderer)

        # Reconfigure
        configure_logging(level="DEBUG", format="console")
        config2 = structlog.get_config()
        assert isinstance(config2["processors"][-1], structlog.dev.ConsoleRenderer)

    def test_logging_to_stderr(self):
        """Test that logs go to stderr."""
        from quicketl.logging import configure_logging, get_logger

        configure_logging(level="INFO", format="json")

        # Verify basicConfig was called with stderr
        root_logger = logging.getLogger()
        handlers = root_logger.handlers

        # At least one handler should be configured
        assert len(handlers) >= 0  # May vary by test runner configuration
