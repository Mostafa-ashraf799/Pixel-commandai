"""
Logger
------
نظام سجلات مركزي لكل الأحداث: Errors, Warnings, Info, Debug, AI Actions, Commands.
يحفظ في ~/.cai/logs/cai.log
"""

import logging
import os
from pathlib import Path


_LOGGER_NAME = "cai"
_configured = False


def get_logger(log_level: str = "info") -> logging.Logger:
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)

    if not _configured:
        base_dir = Path(os.path.expanduser("~/.cai/logs"))
        base_dir.mkdir(parents=True, exist_ok=True)
        log_file = base_dir / "cai.log"

        level = getattr(logging, log_level.upper(), logging.INFO)
        logger.setLevel(level)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        _configured = True

    return logger


def log_command(command: str, risk: str) -> None:
    get_logger().info(f"COMMAND | risk={risk} | {command}")


def log_ai_action(action: str, detail: str = "") -> None:
    get_logger().info(f"AI_ACTION | {action} | {detail}")


def log_error(message: str) -> None:
    get_logger().error(message)
