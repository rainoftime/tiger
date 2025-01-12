import unittest
import semantic_analysis.types as sem
from parser.parser import SyntacticError
from semantic_analysis.analyzers import SemanticError
from typing import Type, List, Union

from tests.utils.compilation_steps import semantic_analysis


class TestTypeChecking(unittest.TestCase):
    def test_example_1(self):
        self._assert_is_expected_type(self._type_check("test1.tig"), sem.VoidType)

    def test_example_2(self):
        self._assert_is_expected_type(self._type_check("test2.tig"), sem.VoidType)

    def test_example_3(self):
        self._assert_is_expected_type(self._type_check("test3.tig"), sem.VoidType)

    def test_example_4(self):
        self._assert_is_expected_type(self._type_check("test4.tig"), sem.IntType)

    def test_example_5(self):
        self._assert_is_expected_type(self._type_check("test5.tig"), sem.VoidType)

    def test_example_6(self):
        self._assert_is_expected_type(self._type_check("test6.tig"), sem.VoidType)

    def test_example_7(self):
        self._assert_is_expected_type(self._type_check("test7.tig"), sem.IntType)

    def test_example_8(self):
        self._assert_is_expected_type(self._type_check("test8.tig"), sem.IntType)

    def test_example_9(self):
        self.assertEqual(
            self._type_check("test9.tig"),
            "Compilation error! Then and Else branches of an If expression must return values "
            + "of the same type in line 3",
        )

    def test_example_10(self):
        self.assertEqual(
            self._type_check("test10.tig"),
            "Compilation error! While body must produce no value in line 2",
        )

    def test_example_11(self):
        self.assertEqual(
            self._type_check("test11.tig"),
            "Compilation error! Ending value for loop variable in a For expression must be "
            + "an Integer in line 2",
        )

    def test_example_12(self):
        self._assert_is_expected_type(self._type_check("test12.tig"), sem.VoidType)

    def test_example_13(self):
        self.assertEqual(
            self._type_check("test13.tig"),
            "Compilation error! Values must be of the same type to test for equality or order "
            + "in line 3",
        )

    def test_example_14(self):
        self.assertEqual(
            self._type_check("test14.tig"),
            "Compilation error! Values must be of the same type to test for equality or order "
            + "in line 12",
        )

    def test_example_15(self):
        self.assertEqual(
            self._type_check("test15.tig"),
            "Compilation error! Then branch of an If expression must produce no value when "
            + "there is no Else branch in line 3",
        )

    def test_example_16(self):
        self.assertEqual(
            self._type_check("test16.tig"),
            "Compilation error! Cyclic type definition found involving type a in line 4",
        )

    def test_example_17(self):
        self.assertEqual(
            self._type_check("test17.tig"),
            "Compilation error! Undefined record field type treelist in line 4",
        )

    def test_example_18(self):
        self.assertEqual(
            self._type_check("test18.tig"),
            "Compilation error! Undefined function do_nothing2 in line 5",
        )

    def test_example_19(self):
        self.assertEqual(
            self._type_check("test19.tig"),
            "Compilation error! Undefined variable a in line 8",
        )

    def test_example_20(self):
        self.assertEqual(
            self._type_check("test20.tig"),
            "Compilation error! Undefined variable i in line 3",
        )

    def test_example_21(self):
        self.assertEqual(
            self._type_check("test21.tig"),
            "Compilation error! Right arithmetic operand must be an Integer in line 8",
        )

    def test_example_22(self):
        self.assertEqual(
            self._type_check("test22.tig"),
            "Compilation error! Unknown record field name nam for variable in line 7",
        )

    def test_example_23(self):
        self.assertEqual(
            self._type_check("test23.tig"),
            "Compilation error! Trying to assign a value to a variable of a different type "
            + "in line 7",
        )

    def test_example_24(self):
        self.assertEqual(
            self._type_check("test24.tig"),
            "Compilation error! Trying to access a subscript of a variable that is not an array "
            + "in line 5",
        )

    def test_example_25(self):
        self.assertEqual(
            self._type_check("test25.tig"),
            "Compilation error! Trying to access the f field of a variable that is not a record "
            + "in line 5",
        )

    def test_example_26(self):
        self.assertEqual(
            self._type_check("test26.tig"),
            "Compilation error! Right arithmetic operand must be an Integer in line 3",
        )

    def test_example_27(self):
        self._assert_is_expected_type(self._type_check("test27.tig"), sem.IntType)

    def test_example_28(self):
        self.assertEqual(
            self._type_check("test28.tig"),
            "Compilation error! Initial value for variable rec1 is not of its declared type "
            + "rectype1 in line 7",
        )

    def test_example_29(self):
        self.assertEqual(
            self._type_check("test29.tig"),
            "Compilation error! Initial value for variable arr1 is not of its declared type "
            + "arrtype1 in line 7",
        )

    def test_example_30(self):
        self._assert_is_expected_type(self._type_check("test30.tig"), sem.IntType)

    def test_example_31(self):
        self.assertEqual(
            self._type_check("test31.tig"),
            "Compilation error! Initial value for variable a is not of its declared type int "
            + "in line 3",
        )

    def test_example_32(self):
        self.assertEqual(
            self._type_check("test32.tig"),
            "Compilation error! Array initial value must be of its declared type in line 6",
        )

    def test_example_33(self):
        self.assertEqual(
            self._type_check("test33.tig"),
            "Compilation error! Undefined record type rectype in line 3",
        )

    def test_example_34(self):
        self.assertEqual(
            self._type_check("test34.tig"),
            "Compilation error! Wrong type for argument in position 0 in call to g in line 5",
        )

    def test_example_35(self):
        self.assertEqual(
            self._type_check("test35.tig"),
            "Compilation error! Wrong number of arguments in function call to g, 2 expected, "
            + "but 1 given in line 5",
        )

    def test_example_36(self):
        self.assertEqual(
            self._type_check("test36.tig"),
            "Compilation error! Wrong number of arguments in function call to g, 2 expected, "
            + "but 3 given in line 5",
        )

    def test_example_37(self):
        self._assert_is_expected_type(self._type_check("test37.tig"), sem.IntType)

    def test_example_38(self):
        self.assertEqual(
            self._type_check("test38.tig"),
            "Compilation error! All names in the type declaration block must be unique in line 5",
        )

    def test_example_39(self):
        self.assertEqual(
            self._type_check("test39.tig"),
            "Compilation error! All names in the function declaration block must be unique "
            + "in line 5",
        )

    def test_example_40(self):
        self.assertEqual(
            self._type_check("test40.tig"),
            "Compilation error! Function g returns a value of a type different than "
            + "its declared type in line 3",
        )

    def test_example_41(self):
        self._assert_is_expected_type(self._type_check("test41.tig"), sem.IntType)

    def test_example_42(self):
        self._assert_is_expected_type(self._type_check("test42.tig"), sem.VoidType)

    def test_example_43(self):
        self.assertEqual(
            self._type_check("test43.tig"),
            "Compilation error! Left arithmetic operand must be an Integer in line 6",
        )

    def test_example_44(self):
        self._assert_is_expected_type(self._type_check("test44.tig"), sem.VoidType)

    def test_example_45(self):
        self.assertEqual(
            self._type_check("test45.tig"),
            "Compilation error! Must declare the type of variable a when initializing it to nil "
            + "in line 5",
        )

    def test_example_46(self):
        self._assert_is_expected_type(self._type_check("test46.tig"), sem.IntType)

    def test_example_47(self):
        self._assert_is_expected_type(self._type_check("test47.tig"), sem.IntType)

    def test_example_48(self):
        self._assert_is_expected_type(self._type_check("test48.tig"), sem.IntType)

    def test_example_49(self):
        self.assertEqual(
            self._type_check("test49.tig"),
            "Syntax error in input! Unexpected value nil in line 5",
        )

    def test_example_50(self):
        self._assert_is_expected_type(self._type_check("test50.tig"), sem.IntType)

    def test_example_51(self):
        self._assert_is_expected_type(self._type_check("test51.tig"), sem.VoidType)

    def test_example_52(self):
        self._assert_is_expected_type(self._type_check("test52.tig"), sem.IntType)

    def test_example_53(self):
        self._assert_is_expected_type(self._type_check("test53.tig"), sem.IntType)

    def test_example_54(self):
        self._assert_is_expected_type(self._type_check("test54.tig"), sem.IntType)

    def test_example_55(self):
        self._assert_is_expected_type(self._type_check("test55.tig"), sem.IntType)

    def test_example_56(self):
        self._assert_is_expected_type(self._type_check("test56.tig"), sem.IntType)

    def test_example_57(self):
        self._assert_is_expected_type(self._type_check("test57.tig"), sem.IntType)

    def test_example_58(self):
        self._assert_is_expected_type(self._type_check("test58.tig"), sem.IntType)

    def test_example_59(self):
        self._assert_is_expected_type(self._type_check("test59.tig"), sem.IntType)

    def test_example_60(self):
        self._assert_is_expected_type(self._type_check("test60.tig"), sem.VoidType)

    def test_example_61(self):
        self._assert_is_expected_type(self._type_check("test61.tig"), sem.IntType)

    def test_example_62(self):
        self._assert_is_expected_type(self._type_check("test62.tig"), sem.IntType)

    def test_example_63(self):
        self._assert_is_expected_type(self._type_check("test63.tig"), sem.VoidType)

    def test_example_64(self):
        self._assert_is_expected_type(self._type_check("test64.tig"), sem.IntType)

    def test_example_65(self):
        self._assert_is_expected_type(self._type_check("test65.tig"), sem.IntType)

    def test_example_66(self):
        self._assert_is_expected_type(self._type_check("test66.tig"), sem.IntType)

    def test_example_67(self):
        self._assert_is_expected_type(self._type_check("test67.tig"), sem.IntType)

    def test_example_68(self):
        self._assert_is_expected_type(self._type_check("test68.tig"), sem.IntType)

    def test_example_69(self):
        self._assert_is_expected_type(self._type_check("test69.tig"), sem.VoidType)

    def test_example_70(self):
        self._assert_is_expected_type(self._type_check("test70.tig"), sem.VoidType)

    def test_example_71(self):
        self._assert_is_expected_type(self._type_check("test71.tig"), sem.IntType)

    def test_example_72(self):
        self._assert_is_expected_type(self._type_check("test72.tig"), sem.IntType)

    def test_example_73(self):
        self._assert_is_expected_type(self._type_check("test73.tig"), sem.IntType)

    def test_example_74(self):
        self._assert_is_expected_type(self._type_check("test74.tig"), sem.IntType)

    def test_example_75(self):
        self._assert_is_expected_type(self._type_check("test75.tig"), sem.StringType)

    def test_example_76(self):
        self._assert_is_expected_type(self._type_check("test76.tig"), sem.IntType)

    def test_example_77(self):
        self._assert_is_expected_type(self._type_check("test77.tig"), sem.IntType)

    def test_example_78(self):
        self._assert_is_expected_type(self._type_check("test78.tig"), sem.IntType)

    def test_example_79(self):
        self._assert_is_expected_type(self._type_check("test79.tig"), sem.IntType)

    def test_example_80(self):
        self._assert_is_expected_type(self._type_check("test80.tig"), sem.IntType)

    def test_example_81(self):
        self._assert_is_expected_type(self._type_check("test81.tig"), sem.IntType)

    def test_example_82(self):
        self._assert_is_expected_type(self._type_check("test82.tig"), sem.IntType)

    def test_example_83(self):
        self._assert_is_expected_type(self._type_check("test83.tig"), sem.IntType)

    def test_example_84(self):
        self._assert_is_expected_type(self._type_check("test84.tig"), sem.IntType)

    def test_example_85(self):
        self._assert_is_expected_type(self._type_check("test85.tig"), sem.IntType)

    def test_example_86(self):
        self._assert_is_expected_type(self._type_check("test86.tig"), sem.IntType)

    def test_example_87(self):
        self._assert_is_expected_type(self._type_check("test87.tig"), sem.IntType)

    def test_example_88(self):
        self._assert_is_expected_type(self._type_check("test88.tig"), sem.IntType)

    def test_example_89(self):
        self._assert_is_expected_type(self._type_check("test89.tig"), sem.IntType)

    def test_example_90(self):
        self._assert_is_expected_type(self._type_check("test90.tig"), sem.IntType)

    def test_example_91(self):
        self._assert_is_expected_type(self._type_check("test91.tig"), sem.StringType)

    def test_example_92(self):
        self._assert_is_expected_type(self._type_check("test92.tig"), sem.StringType)

    def test_example_93(self):
        self._assert_is_expected_type(self._type_check("test93.tig"), sem.IntType)

    def test_example_94(self):
        self._assert_is_expected_type(self._type_check("test94.tig"), sem.IntType)

    def test_example_95(self):
        self._assert_is_expected_type(self._type_check("test95.tig"), sem.VoidType)

    def test_example_merge(self):
        self._assert_is_expected_type(self._type_check("merge.tig"), sem.IntType)

    def test_example_queens(self):
        self._assert_is_expected_type(self._type_check("queens.tig"), sem.VoidType)

    def _assert_is_expected_type(
            self, analyzed_type: sem.Type, expected_type: Type[sem.Type]
    ):
        self.assertIsInstance(analyzed_type, expected_type)

    def _assert_is_expected_array(
            self, analyzed_type: sem.Type, array_object_type: Type[sem.Type]
    ):
        self.assertIsInstance(analyzed_type, sem.ArrayType)
        self.assertIsInstance(analyzed_type.type, array_object_type)

    def _assert_is_expected_record(
            self, analyzed_type: sem.Type, record_field_types: List[Type[sem.Type]]
    ):
        self.assertIsInstance(analyzed_type, sem.RecordType)
        for analyzed_field, expected_field in zip(
                analyzed_type.fields, record_field_types
        ):
            self.assertIsInstance(analyzed_field.type, expected_field)

    def _type_check(self, file_name: str) -> Union[str, sem.Type]:
        try:
            analyzed_program = semantic_analysis(file_name)
        except SyntacticError as err:
            return str(err)
        except SemanticError as err:
            return str(err)
        return analyzed_program.type
