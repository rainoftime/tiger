import unittest

from semantic_analysis.table import SymbolTable


class TestSymbolTable(unittest.TestCase):
    def setUp(self):
        self.table = SymbolTable[int]()

    def test_added_value_is_found(self):
        self.table.add("id", 1)

        self.assertEqual(self.table.find("id"), 1)

    def test_not_added_value_is_not_found(self):
        self.assertIsNone(self.table.find("id"))

    def test_last_added_value_is_found(self):
        self.table.add("id", 1)
        self.table.add("id", 2)

        self.assertEqual(self.table.find("id"), 2)

    def test_values_are_still_found_when_adding_scope(self):
        self.table.add("id", 1)
        self.table.begin_scope()

        self.assertEqual(self.table.find("id"), 1)

    def test_ending_scope_recovers_last_value(self):
        self.table.add("id", 1)
        self.table.begin_scope()
        self.table.add("id", 2)

        self.assertEqual(self.table.find("id"), 2)

        self.table.end_scope()

        self.assertEqual(self.table.find("id"), 1)

    def test_value_inside_scope_cannot_be_seen_outside(self):
        self.assertIsNone(self.table.find("id"))

        self.table.begin_scope()
        self.table.add("id", 1)

        self.assertEqual(self.table.find("id"), 1)

        self.table.end_scope()

        self.assertIsNone(self.table.find("id"))

    def test_is_closest_scope_a_loop_when_no_scope(self):
        self.assertFalse(self.table.is_closest_scope_a_loop())

    def test_is_closest_scope_a_loop_when_not_a_loop_scope(self):
        self.table.begin_scope()

        self.assertFalse(self.table.is_closest_scope_a_loop())

    def test_is_closest_scope_a_loop_when_a_loop_scope(self):
        self.table.begin_scope(True)

        self.assertTrue(self.table.is_closest_scope_a_loop())

    def test_is_closest_scope_a_loop_when_nesting_scopes(self):
        self.table.begin_scope()
        self.table.begin_scope(True)

        self.assertTrue(self.table.is_closest_scope_a_loop())

        self.table.begin_scope()

        self.assertFalse(self.table.is_closest_scope_a_loop())
