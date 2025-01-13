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
    
    def display(self) -> str:
        """Return a string representation of the symbol table's current state."""
        result = []
        result.append("Symbol Table Contents:")
        result.append("Bindings:")
        for id, values in self.bindings.items():
            result.append(f"  {id}: {values}")
        result.append("Stack:")
        for item in self.stack:
            if isinstance(item, ScopeStart):
                result.append(f"  SCOPE({'loop' if item.is_loop_scope else 'regular'})")
            else:
                result.append(f"  {item}")
        return "\n".join(result)

    def __str__(self) -> str:
        return self.display()


if __name__ == "__main__":
    table = SymbolTable[int]()
    # Test nested scopes
    table.begin_scope()
    table.add("x", 10)
    table.begin_scope()
    table.add("x", 20)
    print(table.find("x"))  # Should print 20
    table.end_scope()
    print(table.find("x"))  # Should print 10
    table.end_scope()

    # Test loop scopes
    table.begin_scope(is_loop_scope=True)
    table.add("i", 1)
    print(table.is_closest_scope_a_loop())  # Should print True
    # print(table)
    table.begin_scope()
    table.add("i", 2)
    print(table.find("i"))  # Should print 2
    print(table.is_closest_scope_a_loop())  # Should print False
    table.end_scope()
    table.end_scope()
