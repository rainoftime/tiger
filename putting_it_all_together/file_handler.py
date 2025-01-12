from intermediate_representation.fragment import StringFragment
from activation_records.frame import string_literal, temp_to_str
from instruction_selection.assembly import Procedure


class FileHandler:
    def __init__(self, file_name: str):
        self.file = open(file_name, "w")

    def close(self):
        self.file.close()

    def print_data_header(self):
        self.file.write(".section .rodata\n")

    def print_code_header(self):
        self.file.write("\n.text\n")
        self.file.write(".global tigermain\n")
        self.file.write(".type tigermain, @function\n\n")

    def print_string_fragment(self, string_fragment: StringFragment):
        self.file.write(string_literal(string_fragment.label, string_fragment.string))

    def print_assembly_procedure(self, assembly_procedure: Procedure):
        self.file.write(assembly_procedure.format(temp_to_str))
