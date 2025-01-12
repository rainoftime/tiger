import unittest
from typing import List

import intermediate_representation.tree as irt
from canonical.basic_block import basic_block, BasicBlock

from canonical.linearize import linearize
from canonical.trace import trace_schedule
from intermediate_representation.fragment import FragmentManager, ProcessFragment
from tests.utils.compilation_steps import semantic_analysis


class TestTrace(unittest.TestCase):
    """Checks that every conditional jump is followed by its false label and that every statement
    from the basic blocks (except possibly some jumps that were deleted) are in the final list."""

    def setUp(self):
        FragmentManager.fragment_list = []

    def test_example_1(self):
        self._schedule_traces("test1.tig")

    def test_example_2(self):
        self._schedule_traces("test2.tig")

    def test_example_3(self):
        self._schedule_traces("test3.tig")

    def test_example_4(self):
        self._schedule_traces("test4.tig")

    def test_example_5(self):
        self._schedule_traces("test5.tig")

    def test_example_6(self):
        self._schedule_traces("test6.tig")

    def test_example_7(self):
        self._schedule_traces("test7.tig")

    def test_example_8(self):
        self._schedule_traces("test8.tig")

    def test_example_12(self):
        self._schedule_traces("test12.tig")

    def test_example_27(self):
        self._schedule_traces("test27.tig")

    def test_example_30(self):
        self._schedule_traces("test30.tig")

    def test_example_37(self):
        self._schedule_traces("test37.tig")

    def test_example_41(self):
        self._schedule_traces("test41.tig")

    def test_example_42(self):
        self._schedule_traces("test42.tig")

    def test_example_44(self):
        self._schedule_traces("test44.tig")

    def test_example_46(self):
        self._schedule_traces("test46.tig")

    def test_example_47(self):
        self._schedule_traces("test47.tig")

    def test_example_48(self):
        self._schedule_traces("test48.tig")

    def test_example_50(self):
        self._schedule_traces("test50.tig")

    def test_example_51(self):
        self._schedule_traces("test51.tig")

    def test_example_52(self):
        self._schedule_traces("test52.tig")

    def test_example_53(self):
        self._schedule_traces("test53.tig")

    def test_example_54(self):
        self._schedule_traces("test54.tig")

    def test_example_55(self):
        self._schedule_traces("test55.tig")

    def test_example_56(self):
        self._schedule_traces("test56.tig")

    def test_example_57(self):
        self._schedule_traces("test57.tig")

    def test_example_58(self):
        self._schedule_traces("test58.tig")

    def test_example_59(self):
        self._schedule_traces("test59.tig")

    def test_example_60(self):
        self._schedule_traces("test60.tig")

    def test_example_61(self):
        self._schedule_traces("test61.tig")

    def test_example_62(self):
        self._schedule_traces("test62.tig")

    def test_example_63(self):
        self._schedule_traces("test63.tig")

    def test_example_64(self):
        self._schedule_traces("test64.tig")

    def test_example_65(self):
        self._schedule_traces("test65.tig")

    def test_example_66(self):
        self._schedule_traces("test66.tig")

    def test_example_67(self):
        self._schedule_traces("test67.tig")

    def test_example_68(self):
        self._schedule_traces("test68.tig")

    def test_example_69(self):
        self._schedule_traces("test69.tig")

    def test_example_70(self):
        self._schedule_traces("test70.tig")

    def test_example_71(self):
        self._schedule_traces("test71.tig")

    def test_example_72(self):
        self._schedule_traces("test72.tig")

    def test_example_73(self):
        self._schedule_traces("test73.tig")

    def test_example_74(self):
        self._schedule_traces("test74.tig")

    def test_example_75(self):
        self._schedule_traces("test75.tig")

    def test_example_76(self):
        self._schedule_traces("test76.tig")

    def test_example_77(self):
        self._schedule_traces("test77.tig")

    def test_example_78(self):
        self._schedule_traces("test78.tig")

    def test_example_79(self):
        self._schedule_traces("test79.tig")

    def test_example_80(self):
        self._schedule_traces("test80.tig")

    def test_example_81(self):
        self._schedule_traces("test81.tig")

    def test_example_82(self):
        self._schedule_traces("test82.tig")

    def test_example_83(self):
        self._schedule_traces("test83.tig")

    def test_example_84(self):
        self._schedule_traces("test84.tig")

    def test_example_85(self):
        self._schedule_traces("test85.tig")

    def test_example_86(self):
        self._schedule_traces("test86.tig")

    def test_example_87(self):
        self._schedule_traces("test87.tig")

    def test_example_88(self):
        self._schedule_traces("test88.tig")

    def test_example_89(self):
        self._schedule_traces("test89.tig")

    def test_example_90(self):
        self._schedule_traces("test90.tig")

    def test_example_91(self):
        self._schedule_traces("test91.tig")

    def test_example_92(self):
        self._schedule_traces("test92.tig")

    def test_example_93(self):
        self._schedule_traces("test93.tig")

    def test_example_94(self):
        self._schedule_traces("test94.tig")

    def test_example_95(self):
        self._schedule_traces("test95.tig")

    def test_example_merge(self):
        self._schedule_traces("merge.tig")

    def test_example_queens(self):
        self._schedule_traces("queens.tig")

    def _schedule_traces(self, file_name: str):
        semantic_analysis(file_name)
        for fragment in FragmentManager.get_fragments():
            if isinstance(fragment, ProcessFragment):
                blocked_statements = basic_block(linearize(fragment.body))
                traced_statements = trace_schedule(blocked_statements)
                self._assert_conditional_jump_label_placement(traced_statements)
                self._assert_statements_but_jumps_were_not_removed(
                    blocked_statements, traced_statements
                )

    def _assert_conditional_jump_label_placement(self, statements: List[irt.Statement]):
        for index, statement in enumerate(statements):
            if isinstance(statement, irt.ConditionalJump):
                next_statement = statements[index + 1]
                self.assertIsInstance(next_statement, irt.Label)
                self.assertEqual(statement.false, next_statement.label)

    def _assert_statements_but_jumps_were_not_removed(
            self, block: BasicBlock, traced_statements: List[irt.Statement]
    ):
        for statement_list in block.statement_lists:
            for statement in statement_list:
                if not isinstance(statement, irt.Jump):
                    self.assertIn(statement, traced_statements)
