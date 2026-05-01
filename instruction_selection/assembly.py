"""Assembly instruction templates used between code generation and allocation.

The instruction selector does not emit fully formatted strings right away. Instead
it records assembly templates plus the temporary values read and written by each
instruction. Later compiler passes reuse the same objects for:

- flow-graph construction, via the ``source`` and ``destination`` temp lists
- liveness analysis, by treating those lists as use/def sets
- final pretty-printing, by replacing template placeholders after allocation

Template placeholders follow Appel's convention:

- ``'s0``, ``'s1`` ... refer to source temporaries
- ``'d0``, ``'d1`` ... refer to destination temporaries
- ``'j0``, ``'j1`` ... refer to jump labels
"""

from activation_records.temp import Temp, TempLabel
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, List, Optional


class Instruction(ABC):
    """Assembly instruction before temporaries are mapped to concrete registers."""

    @abstractmethod
    def format(self, temp_map: Callable[[Temp], str]) -> str:
        """Render the instruction by replacing placeholders with final names."""
        pass

    def replace(self, prefix: str, replacements: List[str]):
        """Substitute a placeholder family in ``self.line`` in place."""
        for index in range(len(replacements)):
            self.line = self.line.replace(f"{prefix}{index}", replacements[index])


@dataclass
class Operation(Instruction):
    """General-purpose instruction template.

    ``Operation`` covers arithmetic instructions, loads/stores represented as
    operations, calls, and jumps. The allocator and liveness pass treat the
    ``source`` and ``destination`` lists as the instruction's use/def sets.
    """

    line: str
    source: List[Temp]
    destination: List[Temp]
    jump: Optional[List[TempLabel]]

    def format(self, temp_map: Callable[[Temp], str]) -> str:
        self.replace("'s", [temp_map(src) for src in self.source])
        self.replace("'d", [temp_map(dst) for dst in self.destination])
        if self.jump is not None:
            self.replace("'j", self.jump)

        return self.line


@dataclass
class Label(Instruction):
    """Assembler label pseudo-instruction."""

    line: str
    label: TempLabel

    def format(self, temp_map: Callable[[Temp], str]) -> str:
        return self.line


@dataclass
class Move(Instruction):
    """Copy-like instruction kept separate so coalescing can recognize it."""

    line: str
    source: List[Temp]
    destination: List[Temp]

    def format(self, temp_map: Callable[[Temp], str]) -> str:
        self.replace("'s", [temp_map(src) for src in self.source])
        self.replace("'d", [temp_map(dst) for dst in self.destination])

        return self.line


@dataclass
class Procedure:
    """Fully assembled procedure with prologue/body/epilogue fragments."""

    prologue: str
    body: List[Instruction]
    epilogue: str

    def format(self, temp_map: Callable[[Temp], str]) -> str:
        return (
                self.prologue
                + "".join([instruction.format(temp_map) for instruction in self.body])
                + self.epilogue
        )
