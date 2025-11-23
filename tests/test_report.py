# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import io
import unittest

from src.report import (
    _first_items,
    _last_items,
    _top_items_by_mentions,
    _top_players_by_money,
    interactive_loop,
)
from src.state import GameState, ItemStatistics, Player, PlayerRegistry



class ReportHelperTests(unittest.TestCase):
    def test_top_items_by_mentions_orders_and_limits(self):
        stats = ItemStatistics()
        stats.mentions.update({5: 3, 2: 5, 3: 5, 4: 1})
        catalog = {2: "Iron Sword", 3: "Healing Potion", 5: "Arrow"}

        result = _top_items_by_mentions(stats, catalog, limit=3)

        expected = [
            (2, "Iron Sword", 5),
            (3, "Healing Potion", 5),
            (5, "Arrow", 3),
        ]
        self.assertEqual(expected, result)

    def test_top_players_by_money_skips_inactive_and_orders(self):
        player1 = Player(10)
        player1.money = 50
        player1.first_event_ts = 1

        player2 = Player(5)
        player2.money = 75
        player2.first_event_ts = 2

        player3 = Player(7)
        player3.money = 75
        player3.first_event_ts = 3

        inactive = Player(99)  # без событий денег/активности

        result = _top_players_by_money([player1, player2, player3, inactive], limit=3)

        self.assertEqual([player2, player3, player1], result)
        self.assertNotIn(inactive, result)

    def test_first_and_last_items_respect_order_and_limits(self):
        stats = ItemStatistics()
        stats.register_appearance(8, 1700000005)
        stats.register_appearance(2, 1700000001)
        stats.register_appearance(6, 1700000003)
        catalog = {2: "Shield"}

        first_items = _first_items(stats, catalog, limit=2)
        last_items = _last_items(stats, catalog, limit=2)

        self.assertEqual(
            [(8, "unknown item 8", 1700000005), (2, "Shield", 1700000001)],
            first_items,
        )
        self.assertEqual(
            [(2, "Shield", 1700000001), (6, "unknown item 6", 1700000003)],
            last_items,
        )


class InteractiveLoopTests(unittest.TestCase):
    def setUp(self):
        registry = PlayerRegistry(
            {
                1: Player(1, name="Alice"),
                2: Player(2, name="Bob"),
                3: Player(3, name="Charlie"),
            }
        )

        registry.get(1).inventory[100] = 5
        registry.get(2).inventory[100] = 3
        registry.get(3).inventory[100] = 1

        stats = ItemStatistics()
        stats.totals[100] = 9
        stats.owner_counts[100] = 3

        self.game_state = GameState(registry, stats)
        self.catalog = {100: "Magic Sword"}

    def test_interactive_loop_outputs_stats_for_valid_item(self):
        output = io.StringIO()
        interactive_loop(
            self.game_state,
            self.catalog,
            input_stream=io.StringIO("100\n"),
            output_stream=output,
        )

        lines = output.getvalue().splitlines()
        self.assertEqual(
            [
                "Название предмета: Magic Sword",
                "Общее количество в игре: 9",
                "Количество владельцев: 3",
                "Топ 10 игроков по предмету:",
                "Alice, 5",
                "Bob, 3",
                "Charlie, 1",
            ],
            lines,
        )

    def test_interactive_loop_handles_non_numeric_and_continues(self):
        output = io.StringIO()
        interactive_loop(
            self.game_state,
            self.catalog,
            input_stream=io.StringIO("abc\n100\n"),
            output_stream=output,
        )

        lines = output.getvalue().splitlines()
        self.assertEqual(
            [
                "Некорректный item_type_id: abc",
                "Название предмета: Magic Sword",
                "Общее количество в игре: 9",
                "Количество владельцев: 3",
                "Топ 10 игроков по предмету:",
                "Alice, 5",
                "Bob, 3",
                "Charlie, 1",
            ],
            lines,
        )


if __name__ == "__main__":
    unittest.main()