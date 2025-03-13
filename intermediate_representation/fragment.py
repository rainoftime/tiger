from abc import ABC
from typing import List

from dataclasses import dataclass

from activation_records.frame import Frame
from activation_records.temp import TempLabel
from intermediate_representation.tree import Statement


class Fragment(ABC):
    pass


@dataclass
class StringFragment(Fragment):
    label: TempLabel
    string: str


@dataclass
class ProcessFragment(Fragment):
    body: Statement
    frame: Frame


class FragmentManager(ABC):
    fragment_list = []

    @classmethod
    def add_fragment(cls, fragment: Fragment):
        cls.fragment_list.append(fragment)

    @classmethod
    def get_fragments(cls) -> List[Fragment]:
        return cls.fragment_list

    @classmethod
    def reset(cls):
        cls.fragment_list = []
