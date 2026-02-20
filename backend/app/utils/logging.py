"""
utils/logging.py – Structured JSON logging using structlog.
"""
import logging
import sys

import structlog


def configure_logging(environment: str = "development") -> None:
    """Configure structlog for the application."""
    log_level = logging.DEBUG if environment == "development" else logging.INFO

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if environment == "production":
        # JSON output for log aggregation (Datadog, Logstash, etc.)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Human-readable console output for dev
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """Get a named structured logger."""
    return structlog.get_logger(name)
