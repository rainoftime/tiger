from typing import List, Set, Dict

from dataclasses import dataclass

from activation_records.temp import Temp
from instruction_selection.assembly import Instruction, Operation, Move, Label
from liveness_analysis.graph import Graph


class AssemblerInformation:
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
    flow_graph: Graph[AssemblerInformation]  # The flow graph
    temp_uses: Dict[Temp, List[Instruction]]  # The uses of each Temp
    temp_definitions: Dict[Temp, List[Instruction]]  #  The definitions of each Temp


def assembler_flow_graph(instructions: List[Instruction]) -> FlowGraphResult:
    graph = Graph[AssemblerInformation]()
    temp_uses = {}
    temp_definitions = {}
    label_nodes = {}

    # Node creation
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

    # Edge creation
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

    # Liveness iteration
    continue_iteration = True
    while continue_iteration:
        continue_iteration = False
        for node in node_list:
            # Backup live_in and live_out
            backup_live_in = node.information.live_in
            backup_live_out = node.information.live_out

            # Compute live_in and live_out
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
