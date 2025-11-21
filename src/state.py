# -*- coding: utf-8 -*-
"""Модели состояния игроков и предметов.

Модуль предоставляет классы для хранения состояния игроков, применения событий
из логов и накопления статистики по предметам. Предусмотрена поддержка
отрицательного баланса денег, учёт владельцев предметов и отслеживание момента
первого появления предметов в логах.
"""
from __future__ import unicode_literals

import json
from collections import defaultdict


class Player(object):
    """Состояние игрока: имя/уровень, баланс денег и инвентарь."""

    __slots__ = [
        "player_id",
        "name",
        "level",
        "money",
        "inventory",
        "first_event_ts",
        "last_event_ts",
    ]

    def __init__(self, player_id, name=None, level=None):
        self.player_id = player_id
        self.name = name or "unknown"
        self.level = level
        self.money = 0
        self.inventory = defaultdict(int)
        self.first_event_ts = None
        self.last_event_ts = None

    def update_activity(self, timestamp):
        """Зафиксировать время первого и последнего события."""

        if self.first_event_ts is None:
            self.first_event_ts = timestamp
        self.last_event_ts = timestamp

    def apply_money(self, action, amount, timestamp):
        """Применить денежное событие к игроку."""

        self.update_activity(timestamp)
        if action == "MONEY_ADD":
            self.money += amount
        elif action == "MONEY_REMOVE":
            self.money -= amount

    def apply_inventory(self, action, items, timestamp):
        """Применить событие инвентаря и вернуть изменения по предметам."""

        self.update_activity(timestamp)
        multiplier = 1 if action == "ITEM_ADD" else -1
        changes = {}
        for item_type_id, amount in items:
            delta = multiplier * amount
            previous = self.inventory.get(item_type_id, 0)
            updated = previous + delta
            self.inventory[item_type_id] = updated
            changes[item_type_id] = (delta, previous, updated)
        return changes

    def get_item_count(self, item_type_id):
        """Получить количество предметов данного типа у игрока."""

        return self.inventory.get(item_type_id, 0)


class PlayerRegistry(object):
    """Реестр игроков с загрузкой из db.json."""

    def __init__(self, players=None):
        self._players = players or {}

    @classmethod
    def from_db_file(cls, path):
        """Создать реестр игроков на основе файла db.json."""

        with open(path, "r") as handle:
            payload = json.load(handle)
        mapping = {}
        for entry in payload.get("players", []):
            mapping[entry.get("id")] = Player(
                entry.get("id"), entry.get("name"), entry.get("level")
            )
        return cls(mapping)

    def get(self, player_id):
        """Получить игрока по идентификатору, создавая заглушку при отсутствии."""

        if player_id not in self._players:
            self._players[player_id] = Player(player_id)
        return self._players[player_id]

    def values(self):
        """Итерация по всем игрокам."""

        return self._players.values()


class ItemStatistics(object):
    """Глобальная статистика по предметам."""

    def __init__(self):
        self.totals = defaultdict(int)
        self.owner_counts = defaultdict(int)
        self.mentions = defaultdict(int)
        self._first_seen_ts = {}
        self._first_seen_order = []

    def register_appearance(self, item_type_id, timestamp):
        """Зафиксировать первое появление предмета в логах."""

        if item_type_id in self._first_seen_ts:
            return
        self._first_seen_ts[item_type_id] = timestamp
        self._first_seen_order.append((timestamp, item_type_id))

    def record_delta(self, item_type_id, delta):
        """Изменить общий счётчик предметов."""

        self.totals[item_type_id] += delta

    def record_mention(self, item_type_id):
        """Учитывать факт появления предмета в логах (для топа упоминаний)."""

        self.mentions[item_type_id] += 1

    def update_owner_count(self, item_type_id, previous, updated):
        """Скорректировать количество владельцев предмета."""

        if previous <= 0 and updated > 0:
            self.owner_counts[item_type_id] += 1
        elif previous > 0 and updated <= 0:
            self.owner_counts[item_type_id] -= 1
            if self.owner_counts[item_type_id] < 0:
                self.owner_counts[item_type_id] = 0

    def first_items(self, limit=10):
        """Вернуть первые ``limit`` предметов по времени появления."""

        return self._first_seen_order[:limit]

    def last_items(self, limit=10):
        """Вернуть последние ``limit`` предметов по времени появления."""

        if not self._first_seen_order:
            return []
        return self._first_seen_order[-limit:]


class GameState(object):
    """Комбинированное состояние игроков и глобальных счётчиков."""

    def __init__(self, player_registry, item_stats=None):
        self.players = player_registry
        self.item_stats = item_stats or ItemStatistics()

    def apply_inventory_event(self, event):
        """Обработать событие инвентаря из ``InventoryEvent``."""

        player = self.players.get(event.player_id)
        changes = player.apply_inventory(event.action, event.items, event.timestamp)
        for item_type_id, change in changes.items():
            delta, previous, updated = change
            self.item_stats.register_appearance(item_type_id, event.timestamp)
            self.item_stats.record_mention(item_type_id)
            self.item_stats.record_delta(item_type_id, delta)
            self.item_stats.update_owner_count(item_type_id, previous, updated)

    def apply_money_event(self, event):
        """Обработать событие денег из ``MoneyEvent``."""

        player = self.players.get(event.player_id)
        player.apply_money(event.action, event.amount, event.timestamp)


__all__ = [
    "GameState",
    "ItemStatistics",
    "Player",
    "PlayerRegistry",
]
