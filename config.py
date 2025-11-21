# -*- coding: utf-8 -*-
"""Централизованные пути и настройки проекта.

Все пути вычисляются относительно корня репозитория, чтобы упрощать доступ
к исходным данным, справочным файлам и результирующим артефактам обработки.
"""
from __future__ import unicode_literals

import os

# Базовые директории
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
REFERENCE_DIR = os.path.join(DATA_DIR, "reference")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")

# Путь до файла логов в корне репозитория
LOG_FILE_PATH = os.path.join(BASE_DIR, "app.log")

# Пути до исходных логов
INVENTORY_LOG_PATH = os.path.join(RAW_DATA_DIR, "inventory_logs.txt")
MONEY_LOG_PATH = os.path.join(RAW_DATA_DIR, "money_logs.txt")

# Пути до справочных данных
PLAYER_DB_PATH = os.path.join(REFERENCE_DIR, "db.json")
ITEMS_XML_PATH = os.path.join(REFERENCE_DIR, "items.xml")

# Пути до результирующих файлов
COMBINED_LOG_PATH = os.path.join(OUTPUT_DIR, "combined_log.txt")
OUTPUT_STATS_PATH = os.path.join(OUTPUT_DIR, "output.txt")

__all__ = [
    "BASE_DIR",
    "DATA_DIR",
    "RAW_DATA_DIR",
    "REFERENCE_DIR",
    "OUTPUT_DIR",
    "INVENTORY_LOG_PATH",
    "MONEY_LOG_PATH",
    "PLAYER_DB_PATH",
    "ITEMS_XML_PATH",
    "COMBINED_LOG_PATH",
    "OUTPUT_STATS_PATH",
    "LOG_FILE_PATH",
]
