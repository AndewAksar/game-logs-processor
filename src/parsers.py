# -*- coding: utf-8 -*-
"""Потоковые парсеры логов предметов и денег.

Модуль реализует генераторы, которые читают логи построчно, валидируют
формат записей и возвращают структурированные события. Парсеры устойчивы к
ошибочным строкам, не загружают файлы в память и подходят для обработки
объёма до 10 млн записей.
"""
from __future__ import unicode_literals

import logging
import re
from collections import namedtuple


logger = logging.getLogger(__name__)


InventoryEvent = namedtuple(
    "InventoryEvent",
    ["timestamp", "player_id", "action", "items", "line_no", "raw_line"],
)
MoneyEvent = namedtuple(
    "MoneyEvent",
    ["timestamp", "player_id", "action", "amount", "reason", "line_no", "raw_line"],
)


_INVENTORY_LINE_RE = re.compile(
    r"^\[(\d+)\]\s*(ITEM_ADD|ITEM_REMOVE)\s*\|\s*(\d+),\s*\((.*)\)\s*$"
)
_MONEY_ALLOWED_ACTIONS = set(["MONEY_ADD", "MONEY_REMOVE"])


def parse_inventory_line(line, line_no=None, log=None):
    """Разобрать строку лога предметов и вернуть ``InventoryEvent`` или ``None``.

    Строки, не соответствующие формату, пропускаются с предупреждением в логах.
    Возвращает ``None`` при ошибке разбора.
    """

    active_logger = log or logger
    text = line.strip()
    if not text:
        return None

    match = _INVENTORY_LINE_RE.match(text)
    if not match:
        active_logger.warning("Неверный формат строки инвентаря (строка %s): %s", line_no, text)
        return None

    try:
        timestamp = int(match.group(1))
        action = match.group(2)
        player_id = int(match.group(3))
    except ValueError as exc:
        active_logger.warning("Ошибка преобразования заголовка (строка %s): %s", line_no, exc)
        return None

    items_blob = match.group(4)
    items_tokens = [token.strip() for token in items_blob.split(",") if token.strip()]
    if len(items_tokens) % 2 != 0:
        active_logger.warning(
            "Нечётное количество значений предметов (строка %s): %s", line_no, text
        )
        return None

    items = []
    try:
        for idx in range(0, len(items_tokens), 2):
            item_type_id = int(items_tokens[idx])
            amount = int(items_tokens[idx + 1])
            items.append((item_type_id, amount))
    except ValueError as exc:
        active_logger.warning("Ошибка разбора предметов (строка %s): %s", line_no, exc)
        return None

    return InventoryEvent(timestamp, player_id, action, items, line_no, text)


def parse_money_line(line, line_no=None, log=None):
    """Разобрать строку лога денег и вернуть ``MoneyEvent`` или ``None``.

    Строки с неверным форматом или неизвестным действием пропускаются. Причина
    операции допускает наличие пробелов и запятых.
    """

    active_logger = log or logger
    text = line.strip()
    if not text:
        return None

    parts = text.split("|", 2)
    if len(parts) != 3:
        active_logger.warning("Неверный формат строки денег (строка %s): %s", line_no, text)
        return None

    timestamp_raw, player_raw, payload = parts
    payload_parts = payload.split(",", 2)
    if len(payload_parts) != 3:
        active_logger.warning("Неверный формат блока операции (строка %s): %s", line_no, text)
        return None

    action, amount_raw, reason = payload_parts
    action = action.strip()

    if action not in _MONEY_ALLOWED_ACTIONS:
        active_logger.warning("Неизвестное действие денег (строка %s): %s", line_no, text)
        return None

    try:
        timestamp = int(timestamp_raw)
        player_id = int(player_raw)
        amount = int(amount_raw)
    except ValueError as exc:
        active_logger.warning("Ошибка преобразования чисел (строка %s): %s", line_no, exc)
        return None

    return MoneyEvent(timestamp, player_id, action, amount, reason.strip(), line_no, text)


def iter_inventory_events(path, log=None):
    """Потоково читать и парсить ``inventory_logs.txt``.

    Итератор возвращает объекты ``InventoryEvent``. Ошибочные строки пропускаются,
    но не прерывают чтение.
    """

    active_logger = log or logger
    active_logger.info("Чтение inventory лога: %s", path)
    produced = 0
    with open(path, "r") as handle:
        for line_no, line in enumerate(handle, 1):
            event = parse_inventory_line(line, line_no=line_no, log=active_logger)
            if event is not None:
                produced += 1
                yield event
    active_logger.info("Готово: %d событий инвентаря", produced)


def iter_money_events(path, log=None):
    """Потоково читать и парсить ``money_logs.txt``.

    Итератор возвращает объекты ``MoneyEvent``. Ошибочные строки пропускаются,
    но не прерывают чтение.
    """

    active_logger = log or logger
    active_logger.info("Чтение money лога: %s", path)
    produced = 0
    with open(path, "r") as handle:
        for line_no, line in enumerate(handle, 1):
            event = parse_money_line(line, line_no=line_no, log=active_logger)
            if event is not None:
                produced += 1
                yield event
    active_logger.info("Готово: %d событий денег", produced)


__all__ = [
    "InventoryEvent",
    "MoneyEvent",
    "iter_inventory_events",
    "iter_money_events",
    "parse_inventory_line",
    "parse_money_line",
]
