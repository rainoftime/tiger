from dataclasses import dataclass
from typing import TypeVar, Generic, Optional

T = TypeVar("T")


@dataclass
class ScopeStart:
    is_loop_scope: bool


class SymbolTable(Generic[T]):
    def __init__(self):
        self.stack = []
        self.bindings = {}

    def add(self, identifier: str, value: T):
        """Add a new binding to the current scope."""
        self.stack.append(identifier)
        self.bindings[identifier] = self.bindings.get(identifier, []) + [value]

    def find(self, identifier: str) -> Optional[T]:
        """Find the most recent binding for the given identifier."""
        if identifier in self.bindings:
            return self.bindings[identifier][-1]
        return None

    def begin_scope(self, is_loop_scope: bool = False):
        """Begin a new scope."""
        self.stack.append(ScopeStart(is_loop_scope))

    def end_scope(self):
        """End the current scope.Remove all bindings in the current scope."""
        while len(self.stack) > 0 and not isinstance(self.stack[-1], ScopeStart):
            identifier = self.stack.pop(-1)
            self.bindings[identifier].pop(-1)
            if not len(self.bindings[identifier]):
                self.bindings.pop(identifier)
        if len(self.stack):
            self.stack.pop(-1)

    def is_closest_scope_a_loop(self) -> bool:
        index = len(self.stack) - 1
        while index >= 0 and not isinstance(self.stack[index], ScopeStart):
            index -= 1
        return index >= 0 and self.stack[index].is_loop_scope
