"""
Simple logging setup with correlation IDs for tracing requests across services.
Uses Python's built-in logging - Railway will capture all output.
"""

import logging
import uuid
from typing import Optional
from contextvars import ContextVar

# Context variable to store correlation ID for the current request
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')


def get_correlation_id() -> str:
    """Get the current correlation ID, or generate a new one."""
    correlation_id = correlation_id_var.get()
    if not correlation_id:
        correlation_id = str(uuid.uuid4())[:8]  # Short UUID for readability
        correlation_id_var.set(correlation_id)
    return correlation_id


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context."""
    correlation_id_var.set(correlation_id)


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to all log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id()  # type: ignore
        return True


def setup_logging(service_name: str, log_level: str = 'INFO') -> None:
    """
    Setup basic logging with correlation IDs.

    Args:
        service_name: Name of the service (e.g., 'gateway', 'upload')
        log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(log_level)

    # Format: [SERVICE] [CORRELATION_ID] [LEVEL] message
    formatter = logging.Formatter(
        '[%(name)s] [%(correlation_id)s] [%(levelname)s] %(message)s'
    )
    handler.setFormatter(formatter)

    # Add filter to inject correlation ID
    handler.addFilter(CorrelationIdFilter())

    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
