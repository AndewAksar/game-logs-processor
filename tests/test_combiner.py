# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
import tempfile
import unittest

CURRENT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir, "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src.combiner import format_inventory_event, format_money_event, merge_logs_to_file
from src.parsers import parse_inventory_line, parse_money_line


class _StubLogger(object):
    def __init__(self):
        self.info_calls = []
        self.warning_calls = []

    def info(self, msg, *args):
        self.info_calls.append((msg, args))

    def warning(self, msg, *args):
        self.warning_calls.append((msg, args))


class MergeLogsToFileTests(unittest.TestCase):
    def test_merge_sorts_and_prioritizes_inventory(self):
        inv_fd, inv_path = tempfile.mkstemp(prefix="inventory", suffix=".txt")
        money_fd, money_path = tempfile.mkstemp(prefix="money", suffix=".txt")
        out_fd, out_path = tempfile.mkstemp(prefix="combined", suffix=".txt")
        os.close(inv_fd)
        os.close(money_fd)
        os.close(out_fd)

        inventory_lines = [
            "[1700000001] ITEM_ADD | 10, (5, 2)\n",
            "[1700000001] ITEM_REMOVE | 11, (6, 1)\n",
            "[1700000002] ITEM_ADD | 12, (7, 3)\n",
        ]
        money_lines = [
            "1700000000|44|MONEY_ADD,100,bonus\n",
            "1700000001|45|MONEY_REMOVE,10,fee\n",
        ]

        try:
            with open(inv_path, "w") as inv_handle:
                inv_handle.writelines(inventory_lines)
            with open(money_path, "w") as money_handle:
                money_handle.writelines(money_lines)

            logger = _StubLogger()
            merge_logs_to_file(inv_path, money_path, out_path, log=logger)

            with open(out_path, "r") as combined_handle:
                combined_lines = [line.rstrip("\n") for line in combined_handle]

            inventory_events = [
                parse_inventory_line(line, line_no=index + 1) for index, line in enumerate(inventory_lines)
            ]
            money_events = [
                parse_money_line(line, line_no=index + 1) for index, line in enumerate(money_lines)
            ]
            expected_lines = [
                format_money_event(money_events[0]),
                format_inventory_event(inventory_events[0]),
                format_inventory_event(inventory_events[1]),
                format_money_event(money_events[1]),
                format_inventory_event(inventory_events[2]),
            ]

            self.assertEqual(expected_lines, combined_lines)
        finally:
            os.remove(inv_path)
            os.remove(money_path)
            os.remove(out_path)

    def test_merge_handles_empty_inputs(self):
        inv_fd, inv_path = tempfile.mkstemp(prefix="inventory_empty", suffix=".txt")
        money_fd, money_path = tempfile.mkstemp(prefix="money_empty", suffix=".txt")
        out_fd, out_path = tempfile.mkstemp(prefix="combined_empty", suffix=".txt")
        os.close(inv_fd)
        os.close(money_fd)
        os.close(out_fd)

        try:
            logger = _StubLogger()
            merge_logs_to_file(inv_path, money_path, out_path, log=logger)

            with open(out_path, "r") as combined_handle:
                combined_contents = combined_handle.read()

            self.assertEqual("", combined_contents)
            self.assertTrue(logger.info_calls)
            self.assertEqual((0, 0, 0), logger.info_calls[-1][1])
        finally:
            os.remove(inv_path)
            os.remove(money_path)
            os.remove(out_path)


if __name__ == "__main__":
    unittest.main()