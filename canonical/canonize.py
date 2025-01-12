from typing import List

from canonical.basic_block import basic_block
from canonical.linearize import linearize
from canonical.trace import trace_schedule
from intermediate_representation.tree import Statement


def canonize(statement: Statement) -> List[Statement]:
    return trace_schedule(basic_block(linearize(statement)))
