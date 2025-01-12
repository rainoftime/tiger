from activation_records.temp import Temp, TempLabel
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, List, Optional


# Assembly language instruction without register assignments.
class Instruction(ABC):
    # Returns the instruction as a string, replacing the placeholders with temporaries.
    @abstractmethod
    def format(self, temp_map: Callable[[Temp], str]) -> str:
        pass

    def replace(self, prefix: str, replacements: List[str]):
        for index in range(len(replacements)):
            self.line = self.line.replace(f"{prefix}{index}", replacements[index])


@dataclass
class Operation(Instruction):
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
    line: str
    label: TempLabel

    def format(self, temp_map: Callable[[Temp], str]) -> str:
        return self.line


@dataclass
class Move(Instruction):
    line: str
    source: List[Temp]
    destination: List[Temp]

    def format(self, temp_map: Callable[[Temp], str]) -> str:
        self.replace("'s", [temp_map(src) for src in self.source])
        self.replace("'d", [temp_map(dst) for dst in self.destination])

        return self.line


@dataclass
class Procedure:
    prologue: str
    body: List[Instruction]
    epilogue: str

    def format(self, temp_map: Callable[[Temp], str]) -> str:
        return (
                self.prologue
                + "".join([instruction.format(temp_map) for instruction in self.body])
                + self.epilogue
        )
