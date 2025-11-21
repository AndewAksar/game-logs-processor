# -*- coding: utf-8 -*-
"""Слияние потоков логов предметов и денег в комбинированный файл.

Модуль читает два входных файла построчно, объединяет события по временной
метке (с приоритетом записей инвентаря при совпадении времени) и сразу пишет
строки в ``combined_log.txt`` без накопления в памяти.
"""
from __future__ import unicode_literals

import heapq
import logging
from datetime import datetime

from parsers import iter_inventory_events, iter_money_events


logger = logging.getLogger(__name__)


def _format_timestamp(timestamp):
    """Преобразовать целочисленный timestamp в строку ``[YY-MM-DD HH:MM:SS]``."""

    dt = datetime.utcfromtimestamp(timestamp)
    return dt.strftime("%y-%m-%d %H:%M:%S")


def format_inventory_event(event):
    """Сформатировать строку для события инвентаря."""

    ts = _format_timestamp(event.timestamp)
    items = ["(%d, %d)" % (item_type_id, amount) for item_type_id, amount in event.items]
    return "[%s] %d | %s %s" % (ts, event.player_id, event.action, " ".join(items))


def format_money_event(event):
    """Сформатировать строку для денежного события."""

    ts = _format_timestamp(event.timestamp)
    return "[%s] %d | %s | %d | %s" % (
        ts,
        event.player_id,
        event.action,
        event.amount,
        event.reason,
    )


def merge_logs_to_file(inventory_path, money_path, output_path, log=None):
    """Объединить логи предметов и денег в комбинированный файл.

    Чтение выполняется потоково: в памяти одновременно находятся только по одной
    записи из каждого источника. При одинаковом времени события инвентаря имеют
    более высокий приоритет. Порядок в рамках каждого файла сохраняется за счёт
    дополнительного счётчика.
    """

    active_logger = log or logger
    active_logger.info(
        "Начато слияние логов: inventory=%s, money=%s -> %s",
        inventory_path,
        money_path,
        output_path,
    )
    inventory_iter = iter_inventory_events(inventory_path, log=active_logger)
    money_iter = iter_money_events(money_path, log=active_logger)

    heap = []
    inventory_order = 0
    money_order = 0

    try:
        first_inv = next(inventory_iter)
    except StopIteration:
        first_inv = None
    if first_inv is not None:
        heapq.heappush(heap, (first_inv.timestamp, 0, inventory_order, "inventory", first_inv))
        inventory_order += 1

    try:
        first_money = next(money_iter)
    except StopIteration:
        first_money = None
    if first_money is not None:
        heapq.heappush(heap, (first_money.timestamp, 1, money_order, "money", first_money))
        money_order += 1

    inventory_count = 0
    money_count = 0
    with open(output_path, "w") as handle:
        while heap:
            _, _, _, source, event = heapq.heappop(heap)
            if source == "inventory":
                line = format_inventory_event(event)
                inventory_count += 1
            else:
                line = format_money_event(event)
                money_count += 1
            handle.write(line + "\n")

            if source == "inventory":
                try:
                    next_event = next(inventory_iter)
                except StopIteration:
                    next_event = None
                if next_event is not None:
                    heapq.heappush(
                        heap,
                        (
                            next_event.timestamp,
                            0,
                            inventory_order,
                            "inventory",
                            next_event,
                        ),
                    )
                    inventory_order += 1
            else:
                try:
                    next_event = next(money_iter)
                except StopIteration:
                    next_event = None
                if next_event is not None:
                    heapq.heappush(
                        heap,
                        (
                            next_event.timestamp,
                            1,
                            money_order,
                            "money",
                            next_event,
                        ),
                    )
                    money_order += 1

    active_logger.info(
        "Слияние завершено: %d событий инвентаря, %d событий денег, всего %d",
        inventory_count,
        money_count,
        inventory_count + money_count,
    )

__all__ = ["format_inventory_event", "format_money_event", "merge_logs_to_file"]