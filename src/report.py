# -*- coding: utf-8 -*-
"""Генерация статистики и интерактивный вывод по предметам.

Модуль формирует файл ``output.txt`` с требуемыми разделами и запускает
интерактивный режим для ответов на запросы по ``item_type_id``. Расчёты опираются
на состояние, сформированное при проходе по логам.
"""
from __future__ import unicode_literals

import io
import logging
import sys
from datetime import datetime

try:
    text_type = unicode  # type: ignore[name-defined]
except NameError:  # pragma: no cover - Python 3 fallback
    text_type = str


logger = logging.getLogger(__name__)


def _to_text(value):
    """Преобразовать значение к ``unicode`` для красивого выравнивания."""

    if isinstance(value, text_type):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return text_type(value)


def _write_table(handle, headers, rows, padding=2):
    """Вывести простую таблицу с выравниванием колонок."""

    widths = [len(_to_text(h)) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(_to_text(cell)))

    def _format_row(row_values):
        parts = []
        for idx, cell in enumerate(row_values):
            text = _to_text(cell)
            parts.append(text.ljust(widths[idx]))
        return (" " * padding).join(parts)

    handle.write(_format_row(headers) + "\n")
    handle.write("-" * (sum(widths) + padding * (len(headers) - 1)) + "\n")
    for row in rows:
        handle.write(_format_row(row) + "\n")
    handle.write("\n")
from xml.etree import ElementTree


def _format_timestamp(timestamp):
    """Вернуть строковое представление времени ``[YY-MM-DD HH:MM:SS]``."""

    dt = datetime.utcfromtimestamp(timestamp)
    return dt.strftime("%y-%m-%d %H:%M:%S")


def load_items_catalog(path):
    """Загрузить названия предметов из ``items.xml`` в словарь ``id → name``."""

    logger.info("Загрузка каталога предметов из %s", path)
    tree = ElementTree.parse(path)
    root = tree.getroot()
    catalog = {}
    for item in root.findall("item"):
        item_id_node = item.find("item_type_id")
        name_node = item.find("item_name")
        if item_id_node is None or item_id_node.text is None:
            continue
        try:
            item_id = int(item_id_node.text)
        except (TypeError, ValueError):
            continue

        name = None
        if name_node is not None and name_node.text is not None:
            name = name_node.text.strip()

        catalog[item_id] = name or "unknown"
    logger.info("Каталог загружен: %d предметов", len(catalog))
    return catalog


def _item_name(item_type_id, catalog):
    """Получить название предмета с запасным текстом."""

    return catalog.get(item_type_id, "unknown item %s" % item_type_id)


def _top_items_by_mentions(item_stats, catalog, limit=10):
    """Подготовить топ предметов по количеству упоминаний в логах."""

    ranked = sorted(
        item_stats.mentions.items(), key=lambda pair: (-pair[1], pair[0])
    )
    result = []
    for item_type_id, count in ranked[:limit]:
        result.append((item_type_id, _item_name(item_type_id, catalog), count))
    return result


def _top_players_by_money(players, limit=10):
    """Отсортировать игроков по итоговому балансу денег."""

    active_players = [p for p in players if p.first_event_ts is not None]
    ordered = sorted(active_players, key=lambda p: (-p.money, p.player_id))
    return ordered[:limit]


def _first_items(item_stats, catalog, limit=10):
    """Получить первые ``limit`` предметов по времени появления."""

    result = []
    for timestamp, item_type_id in item_stats.first_items(limit=limit):
        result.append((item_type_id, _item_name(item_type_id, catalog), timestamp))
    return result


def _last_items(item_stats, catalog, limit=10):
    """Получить последние ``limit`` предметов по времени появления."""

    result = []
    for timestamp, item_type_id in item_stats.last_items(limit=limit):
        result.append((item_type_id, _item_name(item_type_id, catalog), timestamp))
    return result


def _write_top_items(handle, game_state, catalog):
    """Сериализовать топ предметов в файловый дескриптор."""

    handle.write("Топ 10 предметов по количеству упоминаний:\n")
    rows = []
    for idx, (item_type_id, name, count) in enumerate(
        _top_items_by_mentions(game_state.item_stats, catalog), start=1
    ):
        owners = game_state.item_stats.owner_counts.get(item_type_id, 0)
        rows.append((idx, name, item_type_id, count, owners))

    _write_table(
        handle,
        ("#", "Название", "item_type_id", "Упоминаний", "Уникальных владельцев"),
        rows,
    )


def _write_top_players(handle, game_state):
    """Сериализовать топ игроков по балансу с датами активности."""

    handle.write("Топ 10 игроков по количеству денег после всех операций:\n")
    rows = []
    for idx, player in enumerate(
        _top_players_by_money(game_state.players.values()), start=1
    ):
        first_ts = (
            _format_timestamp(player.first_event_ts)
            if player.first_event_ts is not None
            else "N/A"
        )
        last_ts = (
            _format_timestamp(player.last_event_ts)
            if player.last_event_ts is not None
            else "N/A"
        )
        rows.append((idx, player.name, player.player_id, player.money, first_ts, last_ts))

    _write_table(
        handle,
        ("#", "Игрок", "player_id", "Баланс", "Первое событие", "Последнее событие"),
        rows,
    )


def _write_first_items(handle, game_state, catalog):
    """Сериализовать первые предметы по времени появления."""

    handle.write("Первые 10 предметов по времени появления:\n")
    rows = []
    for idx, (item_type_id, name, timestamp) in enumerate(
        _first_items(game_state.item_stats, catalog), start=1
    ):
        rows.append((idx, name, item_type_id, _format_timestamp(timestamp)))

    _write_table(
        handle,
        ("#", "Название", "item_type_id", "Время первого появления (UTC)"),
        rows,
    )


def _write_last_items(handle, game_state, catalog):
    """Сериализовать последние предметы по времени появления."""

    handle.write("Последние 10 предметов по времени появления:\n")
    rows = []
    for idx, (item_type_id, name, timestamp) in enumerate(
        _last_items(game_state.item_stats, catalog), start=1
    ):
        rows.append((idx, name, item_type_id, _format_timestamp(timestamp)))

    _write_table(
        handle,
        ("#", "Название", "item_type_id", "Время последнего появления (UTC)"),
        rows,
    )


def write_statistics(game_state, catalog, output_path):
    """Записать файл ``output.txt`` с четырьмя блоками статистики."""

    logger.info(
        "Формирование статистики: игроков=%d, предметов=%d, файл=%s",
        len(game_state.players.values()),
        len(game_state.item_stats.totals),
        output_path,
    )
    with io.open(output_path, "w", encoding="utf-8") as handle:
        _write_top_items(handle, game_state, catalog)
        _write_top_players(handle, game_state)
        _write_first_items(handle, game_state, catalog)
        _write_last_items(handle, game_state, catalog)
    logger.info("Статистика записана в %s", output_path)


def interactive_loop(game_state, catalog, input_stream=None, output_stream=None):
    """Отвечать на запросы ``item_type_id`` из stdin по накопленной статистике."""

    instream = input_stream or sys.stdin
    outstream = output_stream or sys.stdout

    for raw_line in instream:
        line = raw_line.strip()
        if not line:
            continue
        try:
            item_type_id = int(line)
        except ValueError:
            logger.warning("Получен некорректный item_type_id: %s", line)
            outstream.write("Некорректный item_type_id: %s\n" % line)
            outstream.flush()
            continue

        logger.info("Запрос статистики по item_type_id=%d", item_type_id)
        total_count = game_state.item_stats.totals.get(item_type_id, 0)
        owners = game_state.item_stats.owner_counts.get(item_type_id, 0)
        name = _item_name(item_type_id, catalog)

        outstream.write("Название предмета: %s\n" % name)
        outstream.write("Общее количество в игре: %d\n" % total_count)
        outstream.write("Количество владельцев: %d\n" % owners)
        outstream.write("Топ 10 игроков по предмету:\n")

        player_counts = []
        for player in game_state.players.values():
            count = player.get_item_count(item_type_id)
            if count > 0:
                player_counts.append((player, count))

        for player, count in sorted(
            player_counts, key=lambda pair: (-pair[1], pair[0].player_id)
        )[:10]:
            outstream.write("%s, %d\n" % (player.name, count))

        outstream.flush()


__all__ = [
    "interactive_loop",
    "load_items_catalog",
    "write_statistics",
]