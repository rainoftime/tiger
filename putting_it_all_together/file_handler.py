from abc import ABC, abstractmethod
from intermediate_representation.fragment import StringFragment
from instruction_selection.assembly import Procedure

# Support both legacy and architecture-aware imports
try:
    from activation_records.architecture_frame import temp_to_str
    ARCH_SUPPORT = True
except ImportError:
    from activation_records.frame import temp_to_str
    ARCH_SUPPORT = False


class AssemblyOutputHandler(ABC):
    """Abstract base class for architecture-specific assembly output"""
    
    @abstractmethod
    def get_data_header(self) -> str:
        pass
    
    @abstractmethod
    def get_code_header(self) -> str:
        pass
    
    @abstractmethod
    def format_string_literal(self, label: str, string: str) -> str:
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        pass


class X86_64OutputHandler(AssemblyOutputHandler):
    """x86-64 assembly output handler"""
    
    def get_data_header(self) -> str:
        return ".section .rodata\n"
    
    def get_code_header(self) -> str:
        return "\n.text\n.global tigermain\n.type tigermain, @function\n\n"
    
    def format_string_literal(self, label: str, string: str) -> str:
        return f"{label}:\n\t.string \"{string}\"\n"
    
    def get_file_extension(self) -> str:
        return ".s"


class ARM64OutputHandler(AssemblyOutputHandler):
    """ARM64 assembly output handler"""
    
    def get_data_header(self) -> str:
        return ".section .rodata\n"
    
    def get_code_header(self) -> str:
        return "\n.text\n.global tigermain\n.type tigermain, %function\n\n"
    
    def format_string_literal(self, label: str, string: str) -> str:
        return f"{label}:\n\t.asciz \"{string}\"\n"
    
    def get_file_extension(self) -> str:
        return ".s"


class RISCVOutputHandler(AssemblyOutputHandler):
    """RISC-V assembly output handler"""
    
    def get_data_header(self) -> str:
        return ".section .rodata\n"
    
    def get_code_header(self) -> str:
        return "\n.text\n.global tigermain\n.type tigermain, @function\n\n"
    
    def format_string_literal(self, label: str, string: str) -> str:
        return f"{label}:\n\t.string \"{string}\"\n"
    
    def get_file_extension(self) -> str:
        return ".s"


class FileHandler:
    """Unified file handler supporting both legacy and multi-architecture modes"""
    
    def __init__(self, filename: str, output_handler: AssemblyOutputHandler = None):
        if output_handler:
            # Multi-architecture mode
            self.output_handler = output_handler
            if not filename.endswith(output_handler.get_file_extension()):
                filename += output_handler.get_file_extension()
        else:
            # Legacy mode - assume x86-64
            self.output_handler = X86_64OutputHandler()
            if not filename.endswith('.s'):
                filename += '.s' if not filename.endswith('.s') else ''
        
        self.file = open(filename, "w")
    
    def close(self):
        self.file.close()
    
    def print_data_header(self):
        self.file.write(self.output_handler.get_data_header())
    
    def print_code_header(self):
        self.file.write(self.output_handler.get_code_header())
    
    def print_string_fragment(self, string_fragment: StringFragment):
        if hasattr(self.output_handler, 'format_string_literal'):
            # Multi-architecture mode
            output = self.output_handler.format_string_literal(
                string_fragment.label, string_fragment.string
            )
            self.file.write(output)
        else:
            # Legacy mode
            from activation_records.frame import string_literal
            self.file.write(string_literal(string_fragment.label, string_fragment.string))
    
    def print_assembly_procedure(self, assembly_procedure: Procedure):
        self.file.write(assembly_procedure.format(temp_to_str))
    
    def get_file_content(self):
        return self.file


def get_output_handlers():
    """Get dictionary of supported output handlers"""
    return {
        "x86-64": X86_64OutputHandler(),
        "arm64": ARM64OutputHandler(),
        "riscv": RISCVOutputHandler(),
    }


# Backward compatibility aliases
ArchFileHandler = FileHandler
