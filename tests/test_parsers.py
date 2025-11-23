# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import tempfile
import unittest

from src.parsers import (
    InventoryEvent,
    MoneyEvent,
    iter_inventory_events,
    iter_money_events,
    parse_inventory_line,
    parse_money_line,
)


class ParseInventoryLineTests(unittest.TestCase):
    def test_parse_valid_inventory_line(self):
        line = "  [1700000000] ITEM_ADD | 42, (10, 2, 11, 5)  "
        event = parse_inventory_line(line, line_no=7)

        expected = InventoryEvent(1700000000, 42, "ITEM_ADD", [(10, 2), (11, 5)], 7, line.strip())
        self.assertEqual(expected, event)

    def test_parse_inventory_line_empty_returns_none(self):
        self.assertIsNone(parse_inventory_line("   "))

    def test_parse_inventory_line_with_odd_tokens_returns_none(self):
        line = "[1] ITEM_REMOVE | 5, (10, 3, 11)"
        self.assertIsNone(parse_inventory_line(line, line_no=2))

    def test_parse_inventory_line_with_non_numeric_items_returns_none(self):
        line = "[1] ITEM_ADD | 5, (a, 3)"
        self.assertIsNone(parse_inventory_line(line, line_no=3))


class ParseMoneyLineTests(unittest.TestCase):
    def test_parse_valid_money_line(self):
        line = "1700000000|101|MONEY_REMOVE,75, Arena reward "
        event = parse_money_line(line, line_no=4)

        expected = MoneyEvent(1700000000, 101, "MONEY_REMOVE", 75, "Arena reward", 4, line.strip())
        self.assertEqual(expected, event)

    def test_parse_money_line_empty_returns_none(self):
        self.assertIsNone(parse_money_line("   "))

    def test_parse_money_line_with_unknown_action_returns_none(self):
        line = "1700000000|101|BONUS,10,something"
        self.assertIsNone(parse_money_line(line, line_no=5))

    def test_parse_money_line_with_invalid_numbers_returns_none(self):
        line = "not_a_timestamp|101|MONEY_ADD,amount,reason"
        self.assertIsNone(parse_money_line(line, line_no=6))


class IterInventoryEventsTests(unittest.TestCase):
    def test_iter_inventory_events_skips_invalid_lines(self):
        fd, path = tempfile.mkstemp(prefix="inventory", suffix=".txt")
        os.close(fd)
        try:
            with open(path, "w") as handle:
                handle.write("[1] ITEM_ADD | 2, (10, 1)\n")
                handle.write("[2] ITEM_REMOVE | 3, (11, 2, 12)\n")
                handle.write("\n")
                handle.write("[3] ITEM_ADD | 4, (20, 5, 21, 6)\n")

            events = list(iter_inventory_events(path))

            self.assertEqual(2, len(events))
            self.assertEqual(1, events[0].line_no)
            self.assertEqual(4, events[1].player_id)
        finally:
            os.remove(path)


class IterMoneyEventsTests(unittest.TestCase):
    def test_iter_money_events_skips_invalid_lines(self):
        fd, path = tempfile.mkstemp(prefix="money", suffix=".txt")
        os.close(fd)
        try:
            with open(path, "w") as handle:
                handle.write("1700000000|5|MONEY_ADD,10,quest reward\n")
                handle.write("bad line without separators\n")
                handle.write("1700000002|6|UNKNOWN,15,something\n")
                handle.write("1700000003|7|MONEY_REMOVE,3, fee \n")

            events = list(iter_money_events(path))

            self.assertEqual(2, len(events))
            self.assertEqual("MONEY_ADD", events[0].action)
            self.assertEqual("MONEY_REMOVE", events[1].action)
            self.assertEqual("fee", events[1].reason)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()