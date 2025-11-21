# -*- coding: utf-8 -*-
"""Точка входа для полного конвейера обработки логов.

Запускает слияние логов, построение состояния игроков/предметов, генерацию
`output.txt` и интерактивный режим по ``item_type_id``. При старте включает
логирование в корневой файл ``app.log``.
"""

from __future__ import unicode_literals

import logging

from config import (
    INVENTORY_LOG_PATH,
    MONEY_LOG_PATH,
    COMBINED_LOG_PATH,
    OUTPUT_STATS_PATH,
    PLAYER_DB_PATH,
    ITEMS_XML_PATH,
)
from src.combiner import merge_logs_to_file
from src.logging_setup import configure_logging
from src.parsers import iter_inventory_events, iter_money_events
from src.report import load_items_catalog, write_statistics, interactive_loop
from src.state import PlayerRegistry, GameState


logger = logging.getLogger(__name__)


def run_pipeline(interactive=True):
    """Выполнить полный цикл обработки данных."""

    configure_logging()
    logger.info("Запуск конвейера обработки логов")

    logger.info("Слияние инвентарных и денежных логов в %s", COMBINED_LOG_PATH)
    merge_logs_to_file(INVENTORY_LOG_PATH, MONEY_LOG_PATH, COMBINED_LOG_PATH)

    logger.info("Построение состояния игроков и предметов")
    registry = PlayerRegistry.from_db_file(PLAYER_DB_PATH)
    state = GameState(registry)

    for event in iter_inventory_events(INVENTORY_LOG_PATH):
        state.apply_inventory_event(event)
    for event in iter_money_events(MONEY_LOG_PATH):
        state.apply_money_event(event)

    catalog = load_items_catalog(ITEMS_XML_PATH)
    logger.info("Формирование статистики в %s", OUTPUT_STATS_PATH)
    write_statistics(state, catalog, OUTPUT_STATS_PATH)

    if interactive:
        logger.info("Запуск интерактивного режима: ожидается ввод item_type_id")
        print("Введите item_type_id (Ctrl+D/Ctrl+Z — выход):")
        interactive_loop(state, catalog)


if __name__ == "__main__":
    run_pipeline(interactive=True)