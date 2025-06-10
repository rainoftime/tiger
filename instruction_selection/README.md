# Multi-Architecture Code Generation

This module provides code generation support for multiple target architectures, allowing the compiler to generate assembly code for x86-64, ARM64, and RISC-V from the same intermediate representation (IR).

## Architecture Support

### Supported Architectures

1. **x86-64** - Intel/AMD 64-bit architecture with AT&T syntax
2. **ARM64** - ARM 64-bit architecture (AArch64) 
3. **RISC-V** - RISC-V 64-bit architecture

## Architecture Abstraction

The code generation is built around an abstract `Architecture` base class that defines the interface for target-specific code generation:

```python
class Architecture(ABC):
    @abstractmethod
    def convert_relational_operator(self, operator: IRT.RelationalOperator) -> str: ...
    @abstractmethod
    def convert_binary_operator(self, operator: IRT.BinaryOperator) -> str: ...
    @abstractmethod
    def emit_label(self, label: str) -> Assembly.Instruction: ...
    @abstractmethod
    def emit_jump(self, labels: List[str]) -> Assembly.Instruction: ...
    # ... other methods
```

Each target architecture implements this interface with architecture-specific instruction formats, register conventions, and calling conventions.

## Key Architecture Differences

### x86-64 Architecture
- **Syntax**: AT&T syntax (`movq %rax, %rbx`)
- **Register prefix**: `%`
- **Calling convention**: System V ABI
- **Return register**: `rax`
- **Argument registers**: `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9`

### ARM64 Architecture  
- **Syntax**: ARM assembly syntax (`mov x0, x1`)
- **Register prefix**: `x`
- **Calling convention**: AAPCS64
- **Return register**: `x0`
- **Argument registers**: `x0`-`x7`

### RISC-V Architecture
- **Syntax**: RISC-V assembly syntax (`mv a0, a1`)
- **Register prefix**: `x` (or ABI names like `a0`, `t0`)
- **Calling convention**: RISC-V calling convention
- **Return register**: `a0`
- **Argument registers**: `a0`-`a7`

## Usage

### Basic Usage

```python
from instruction_selection.codegen import Codegen, X86_64Architecture, ARMArchitecture, RISCVArchitecture

# Set target architecture
Codegen.set_target_architecture(X86_64Architecture())

# Generate code from IR statements
instructions = Codegen.codegen(ir_statements)
```

### Switching Architectures

```python
# Get all supported architectures
architectures = Codegen.get_supported_architectures()

# Generate code for multiple architectures
for arch_name, arch in architectures.items():
    Codegen.set_target_architecture(arch)
    instructions = Codegen.codegen(ir_statements)
    print(f"{arch_name}: {len(instructions)} instructions")
```

## Example Output

For the same IR, different architectures generate different assembly:

### x86-64 Output
```assembly
start:
movq $10, %'d0
movq $20, %'d1  
movq %'s0, %'d2
addq %'s1, %'d2
cmpq $25, %'s0
jg 'j0
```

### ARM64 Output  
```assembly
start:
mov %'d0, #10
mov %'d1, #20
add %'d2, %'s0, %'s1
cmp %'s0, #25
b.gt 'j0
```

### RISC-V Output
```assembly
start:
li %'d0, 10
li %'d1, 20  
add %'d2, %'s0, %'s1
bgt %'s0, 25, 'j0
```

## Running the Example

To see the multi-architecture code generation in action:

```bash
cd instruction_selection
python3 architecture_example.py
```

This will demonstrate generating assembly code for the same intermediate representation across all supported architectures.

## Extending with New Architectures

To add support for a new architecture:

1. Create a new class inheriting from `Architecture`
2. Implement all abstract methods with architecture-specific logic
3. Add the new architecture to `get_supported_architectures()`

Example:
```python
class MyArchitecture(Architecture):
    @property
    def name(self) -> str:
        return "MyArch"
    
    def convert_binary_operator(self, operator: IRT.BinaryOperator) -> str:
        # Architecture-specific operator mapping
        pass
    
    # ... implement other methods
```

## Integration with Activation Records

The current implementation works with the existing x86-64 frame and register allocation modules. For full support of other architectures, the activation records module would need corresponding architecture-specific implementations for:

- Register sets and calling conventions
- Stack frame layouts  
- ABI-specific parameter passing

## Limitations

- ARM and RISC-V implementations use simplified register handling
- Stack management is basic for non-x86 architectures
- Calling conventions are simplified 
- Some complex instructions may need refinement

These can be improved as the compiler's architecture support matures. 