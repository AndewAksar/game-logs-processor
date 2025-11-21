# -*- coding: utf-8 -*-
"""Настройка логирования с выводом в файл корня репозитория и stdout."""

from __future__ import unicode_literals

import logging
import sys
import os

from config import LOG_FILE_PATH


def configure_logging(level=logging.INFO, log_path=None):
    """Сконфигурировать корневой логгер.

    По умолчанию пишет в ``app.log`` в корне репозитория и дублирует вывод в
    stdout. При повторном вызове дополнительные обработчики не добавляются,
    если уже есть конфигурированный корневой логгер.
    """

    path = log_path or LOG_FILE_PATH

    if os.path.isdir(path):
        path = os.path.join(path, os.path.basename(LOG_FILE_PATH))

    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    root = logging.getLogger()
    root.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    def _has_file_handler(target_path):
        abs_target = os.path.abspath(target_path)
        for handler in root.handlers:
            if isinstance(handler, logging.FileHandler):
                if os.path.abspath(handler.baseFilename) == abs_target:
                    return True
        return False

    if not _has_file_handler(path):
        file_handler = logging.FileHandler(path)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    if not any(
        isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) == sys.stdout
        for h in root.handlers
    ):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

__all__ = ["configure_logging"]