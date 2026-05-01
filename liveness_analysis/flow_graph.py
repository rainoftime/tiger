"""Control-flow and local data-flow information for assembly instructions.

The register allocator works over assembly, not IR. This module builds the
control-flow graph (CFG) for a linear instruction list and annotates each node
with the local sets needed for liveness:

- ``definitions``: temps written by the instruction
- ``uses``: temps read by the instruction
- ``live_in`` / ``live_out``: fixed-point liveness sets populated after CFG build

The resulting graph is the bridge between instruction selection and both
interference-graph construction and register allocation.
"""

from typing import List, Set, Dict

from dataclasses import dataclass

from activation_records.temp import Temp
from instruction_selection.assembly import Instruction, Operation, Move, Label
from liveness_analysis.graph import Graph


class AssemblerInformation:
    """Per-instruction metadata used by the liveness and allocation passes."""

    def __init__(self, instruction: Instruction):
        self.instruction = instruction
        self.definitions = self._instruction_definitions()
        self.uses = self._instruction_uses()
        self.live_in = set()
        self.live_out = set()

    def is_move(self) -> bool:
        return isinstance(self.instruction, Move)

    def is_label(self) -> bool:
        return isinstance(self.instruction, Label)

    def is_jump(self) -> bool:
        return (
                isinstance(self.instruction, Operation)
                and self.instruction.jump is not None
        )

    def set_live_in(self):
        """Computes the live_in set for the instruction."""
        self.live_in = self.uses.union(self.live_out - self.definitions)

    def set_live_out(self, successors_live_ins: List[Set[Temp]]):
        """Computes the live_out set for the instruction."""
        self.live_out = set().union(*successors_live_ins)

    def _instruction_definitions(self) -> Set[Temp]:
        """Returns the set of Temp variables defined by the instruction."""
        if isinstance(self.instruction, (Operation, Move)):
            return set(self.instruction.destination)
        return set()

    def _instruction_uses(self) -> Set[Temp]:
        """Returns the set of Temp variables used by the instruction."""
        if isinstance(self.instruction, (Operation, Move)):
            return set(self.instruction.source)
        return set()


@dataclass
class FlowGraphResult:
    """Bundle returned by ``assembler_flow_graph``.

    Besides the CFG itself, later allocation stages need the reverse mapping
    from temps to the instructions that use or define them. Those maps are also
    produced here so the allocator can reuse them during spill rewriting.
    """

    flow_graph: Graph[AssemblerInformation]  # The flow graph
    temp_uses: Dict[Temp, List[Instruction]]  # The uses of each Temp
    temp_definitions: Dict[Temp, List[Instruction]]  #  The definitions of each Temp


def assembler_flow_graph(instructions: List[Instruction]) -> FlowGraphResult:
    """Build a CFG for a procedure body and solve the liveness equations on it.

    The graph has one node per instruction. Fall-through instructions get an
    edge to the next instruction; jump instructions get edges to each listed
    label target. Once the graph is built, the standard backward data-flow
    equations are iterated to a fixed point:

    - ``live_in = use U (live_out - def)``
    - ``live_out = U successor.live_in``
    """
    graph = Graph[AssemblerInformation]()
    temp_uses = {}
    temp_definitions = {}
    label_nodes = {}

    # Create one CFG node per assembly instruction and collect local use/def
    # information while we still have the linear instruction order available.
    for instruction in instructions:
        node = graph.add_node(AssemblerInformation(instruction))
        if node.information.is_label():
            label_nodes[node.information.instruction.label] = node
        for used_temp in node.information.uses:
            if used_temp not in temp_uses:
                temp_uses[used_temp] = []
            temp_uses[used_temp].append(node.information.instruction)
        for defined_temp in node.information.definitions:
            if defined_temp not in temp_definitions:
                temp_definitions[defined_temp] = []
            temp_definitions[defined_temp].append(node.information.instruction)

    # Add fall-through or jump edges. Labels themselves stay in the instruction
    # stream, so jumps can target the node that owns the label.
    node_list = graph.get_nodes()
    for index, node in enumerate(node_list[:-1]):
        if node.information.is_jump():
            for jump_label in node.information.instruction.jump:
                graph.add_edge(node, label_nodes[jump_label])
        else:
            graph.add_edge(node, node_list[index + 1])
    last_node = node_list[-1]
    if last_node.information.is_jump():
        for jump_label in last_node.information.instruction.jump:
            graph.add_edge(last_node, label_nodes[jump_label])

    # Solve the backward liveness equations by repeated relaxation until a full
    # pass stops changing any node. Iterating over the linear order is enough
    # because the equations are monotone and the sets only grow toward a fixed
    # point.
    continue_iteration = True
    while continue_iteration:
        continue_iteration = False
        for node in node_list:
            # Snapshot the previous state so we can detect convergence.
            backup_live_in = node.information.live_in
            backup_live_out = node.information.live_out

            # ``live_in`` uses the previous ``live_out`` value from the current
            # iteration state; ``live_out`` then joins successor ``live_in`` sets.
            node.information.set_live_in()
            node.information.set_live_out(
                [
                    successor.information.live_in
                    for successor in graph.node_successors(node)
                ]
            )

            if (
                    node.information.live_in != backup_live_in
                    or node.information.live_out != backup_live_out
            ):
                continue_iteration = True

    return FlowGraphResult(graph, temp_uses, temp_definitions)
