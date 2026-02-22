"""
Structured logging factory for the AI Receptionist backend.
"""
import logging
import sys
from datetime import datetime, timezone


class _Formatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def format(self, record):
        record.asctime = self.formatTime(record)
        return f"[{record.asctime}] [{record.name}] [{record.levelname}] {record.getMessage()}"


_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_Formatter())


def get_logger(name: str) -> logging.Logger:
    """Return a logger with structured format: [timestamp] [module] [level] message."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.addHandler(_handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
