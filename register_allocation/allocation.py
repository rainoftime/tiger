from typing import List, Set, Dict, Tuple, TypeVar

from dataclasses import dataclass

from activation_records.frame import Frame, TempMap, frame_pointer
from activation_records.temp import Temp, TempManager
from instruction_selection.assembly import Instruction, Move, Operation

from liveness_analysis.flow_graph import assembler_flow_graph
from liveness_analysis.graph import Graph
from liveness_analysis.liveness import liveness

T = TypeVar("T")


@dataclass
class AllocationResult:
    instructions: List[Instruction]
    temp_to_register: Dict[Temp, Temp]


class RegisterAllocator:
    def __init__(self, frame: Frame):
        self.frame = frame

    def main(self, instructions: List[Instruction]) -> AllocationResult:
        self._initialize_data_structures(instructions)

        while (
                self.simplify_worklist
                or self.worklist_moves
                or self.freeze_worklist
                or self.spill_worklist
        ):
            if self.simplify_worklist:
                self._simplify()
            elif self.worklist_moves:
                self._coalesce()
            elif self.freeze_worklist:
                self._freeze()
            elif self.spill_worklist:
                self._select_spill()

        self._assign_colors()
        if self.spilled_nodes:
            new_instructions = self._rewrite_program(instructions)
            return self.main(new_instructions)

        return AllocationResult(instructions, self.color)

    def _initialize_data_structures(self, instructions: List[Instruction]):
        flow_graph_results = assembler_flow_graph(instructions)
        self.temp_uses: Dict[Temp, List[Instruction]] = flow_graph_results.temp_uses
        self.temp_definitions: Dict[
            Temp, List[Instruction]
        ] = flow_graph_results.temp_definitions

        liveness_results = liveness(flow_graph_results.flow_graph)
        all_temporaries = [
            node.information for node in liveness_results.interference_graph.get_nodes()
        ]

        self.precolored: List[Temp] = list(TempMap.register_to_temp.values())
        self.color_amount: int = len(self.precolored)
        self.initial: List[Temp] = [
            temporary
            for temporary in all_temporaries
            if temporary not in self.precolored
        ]

        self.simplify_worklist: List[Temp] = []
        self.freeze_worklist: List[Temp] = []
        self.spill_worklist: List[Temp] = []
        self.spilled_nodes: List[Temp] = []
        self.coalesced_nodes: List[Temp] = []
        self.colored_nodes: List[Temp] = []
        self.select_stack: List[Temp] = []

        self.coalesced_moves: List[Move] = []
        self.constrained_moves: List[Move] = []
        self.frozen_moves: List[Move] = []
        self.worklist_moves: List[Move] = liveness_results.move_instructions
        self.active_moves: List[Move] = []

        self._initialize_adjacency_structures(liveness_results.interference_graph)
        self.move_list: Dict[Temp, List[Move]] = liveness_results.temporary_to_moves

        self.alias: Dict[Temp, Temp] = {}
        self.color: Dict[Temp, Temp] = {
            temporary: temporary for temporary in self.precolored
        }

        self._make_worklist()

    def _initialize_adjacency_structures(self, interference_graph: Graph[Temp]):
        """Initializes the adjacency structures for the graph."""
        self.adjacencies: Set[Tuple[Temp, Temp]] = set()
        self.adjacent_nodes: Dict[Temp, List[Temp]] = {
            temporary: [] for temporary in self.initial
        }
        self.node_degree: Dict[Temp, int] = {
            temporary: 0 if temporary in self.initial else 999999
            for temporary in self.initial + self.precolored
        }

        for node in interference_graph.get_nodes():
            for neighbor in interference_graph.node_successors(node):
                self._add_edge(node.information, neighbor.information)

    def _add_edge(self, node1: Temp, node2: Temp):
        """Adds an edge between two nodes in the interference graph."""
        if (node1, node2) not in self.adjacencies and node1 != node2:
            self.adjacencies.add((node1, node2))
            self.adjacencies.add((node2, node1))
            if node1 not in self.precolored:
                self.adjacent_nodes[node1].append(node2)
                self.node_degree[node1] = self.node_degree[node1] + 1
            if node2 not in self.precolored:
                self.adjacent_nodes[node2].append(node1)
                self.node_degree[node2] = self.node_degree[node2] + 1

    def _make_worklist(self):
        """Initializes the worklists for the algorithm."""
        for node in self.initial:
            if self.node_degree[node] >= self.color_amount:
                self.spill_worklist.append(node)
            elif self._move_related(node):
                self.freeze_worklist.append(node)
            else:
                self.simplify_worklist.append(node)

    def _node_moves(self, node: Temp) -> List[Move]:
        """."""
        return [
            move
            for move in self.move_list[node]
            if move in self.active_moves or move in self.worklist_moves
        ]

    def _move_related(self, node: Temp) -> bool:
        return len(self._node_moves(node)) > 0

    def _simplify(self):
        """Simplifies the graph by removing nodes with degree less than the color amount."""
        while self.simplify_worklist:
            node = self.simplify_worklist.pop(0)
            self.select_stack.append(node)
            for adjacent_node in self._adjacent(node):
                self._decrement_degree(adjacent_node)

    def _adjacent(self, node: Temp) -> List[Temp]:
        return [
            adjacent_node
            for adjacent_node in self.adjacent_nodes[node]
            if adjacent_node not in self.select_stack
               and adjacent_node not in self.coalesced_nodes
        ]

    def _decrement_degree(self, node: Temp):
        self.node_degree[node] = self.node_degree[node] - 1
        if self.node_degree[node] == self.color_amount - 1:
            self._enable_moves([node] + self._adjacent(node))
            self._maybe_remove_from_list(self.spill_worklist, node)
            if self._move_related(node):
                self.freeze_worklist.append(node)
            else:
                self.simplify_worklist.append(node)

    def _enable_moves(self, nodes: List[Temp]):
        for node in nodes:
            for move in self._node_moves(node):
                if move in self.active_moves:
                    self.active_moves.remove(move)
                    self.worklist_moves.append(move)

    def _coalesce(self):
        """Coalesces nodes in the graph."""
        while self.worklist_moves:
            move = self.worklist_moves.pop(0)
            x = self._get_alias(move.source[0])
            y = self._get_alias(move.destination[0])
            if y in self.precolored:
                u, v = y, x
            else:
                u, v = x, y

            if u == v:
                self.coalesced_moves.append(move)
                self._add_work_list(u)
            elif v in self.precolored or (u, v) in self.adjacencies:
                self.constrained_moves.append(move)
                self._add_work_list(u)
                self._add_work_list(v)
            elif (
                    u in self.precolored
                    and all(self._precolored_coalesceable(t, u) for t in self._adjacent(v))
                    or u not in self.precolored
                    and self._conservative_coalesceable(
                set(self._adjacent(u) + self._adjacent(v))
            )
            ):
                self.coalesced_moves.append(move)
                self._combine(u, v)
                self._add_work_list(u)
            else:
                self.active_moves.append(move)

    def _add_work_list(self, node: Temp):
        if (
                node not in self.precolored
                and not self._move_related(node)
                and self.node_degree[node] < self.color_amount
        ):
            self.freeze_worklist.remove(node)
            self.simplify_worklist.append(node)

    def _precolored_coalesceable(self, node: Temp, precolored_node: Temp) -> bool:
        return (
                self.node_degree[node] < self.color_amount
                or node in self.precolored
                or (node, precolored_node) in self.adjacencies
        )

    def _conservative_coalesceable(self, nodes: Set[Temp]) -> bool:
        significant_node_count = 0
        for node in nodes:
            if self.node_degree[node] >= self.color_amount:
                significant_node_count += 1
        return significant_node_count < self.color_amount

    def _get_alias(self, node: Temp) -> Temp:
        if node in self.coalesced_nodes:
            return self._get_alias(self.alias[node])
        return node

    def _combine(self, u: Temp, v: Temp):
        if v in self.freeze_worklist:
            self.freeze_worklist.remove(v)
        else:
            self.spill_worklist.remove(v)
        self.coalesced_nodes.append(v)
        self.alias[v] = u
        self.move_list[u] = self.move_list[u] + self.move_list[v]
        for adjacent_node in self._adjacent(v):
            self._add_edge(adjacent_node, u)
            self._decrement_degree(adjacent_node)
        if self.node_degree[u] >= self.color_amount and u in self.freeze_worklist:
            self.freeze_worklist.remove(u)
            self.spill_worklist.append(u)

    def _freeze(self):
        while self.freeze_worklist:
            node = self.freeze_worklist.pop(0)
            self.simplify_worklist.append(node)
            self._freeze_moves(node)

    def _freeze_moves(self, node: Temp):
        for move in self._node_moves(node):
            x = self._get_alias(move.source[0])
            y = self._get_alias(move.destination[0])
            v = (
                self._get_alias(x)
                if self._get_alias(y) == self._get_alias(node)
                else self._get_alias(y)
            )
            self.active_moves.remove(move)
            self.frozen_moves.append(move)
            if not self._node_moves(v) and self.node_degree[v] < self.color_amount:
                self.freeze_worklist.remove(v)
                self.simplify_worklist.append(v)

    def _select_spill(self):
        spillable_nodes = [
            node for node in self.spill_worklist if node not in self.precolored
        ]
        spilled_node = min(spillable_nodes, key=self._spill_heuristic)
        self.spill_worklist.remove(spilled_node)
        self.simplify_worklist.append(spilled_node)
        self._freeze_moves(spilled_node)

    def _spill_heuristic(self, node: Temp) -> float:
        return (
                len(self.temp_uses[node]) + len(self.temp_definitions[node])
        ) / self.node_degree[node]

    def _assign_colors(self):
        while self.select_stack:
            node = self.select_stack.pop()
            possible_colors = self.precolored.copy()
            for adjacent_node in self.adjacent_nodes[node]:
                if (
                        self._get_alias(adjacent_node) in self.colored_nodes
                        or self._get_alias(adjacent_node) in self.precolored
                ):
                    adjacent_node_color = self.color[self._get_alias(adjacent_node)]
                    self._maybe_remove_from_list(possible_colors, adjacent_node_color)
            if not possible_colors:
                self.spilled_nodes.append(node)
            else:
                self.colored_nodes.append(node)
                self.color[node] = possible_colors[0]
        for node in self.coalesced_nodes:
            self.color[node] = self.color[self._get_alias(node)]

    def _rewrite_program(self, instructions: List[Instruction]) -> List[Instruction]:
        for node in self.spilled_nodes:
            memory_access = self.frame.alloc_local(True)
            for use_instruction in self.temp_uses[node]:
                new_temporary = TempManager.new_temp()
                use_instruction.source = [
                    source_temp if source_temp != node else new_temporary
                    for source_temp in use_instruction.source
                ]
                fetch_instruction = Operation(
                    f"movq {memory_access.offset}(%'s0), %'d0\n",
                    [frame_pointer()],
                    [new_temporary],
                    None,
                )
                instructions.insert(
                    instructions.index(use_instruction), fetch_instruction
                )

            for definition_instruction in self.temp_definitions[node]:
                new_temporary = TempManager.new_temp()
                definition_instruction.destination = [
                    destination_temp if destination_temp != node else new_temporary
                    for destination_temp in definition_instruction.destination
                ]
                store_instruction = Operation(
                    f"movq %'s0, {memory_access.offset}(%'s1)\n",
                    [new_temporary, frame_pointer()],
                    [],
                    None,
                )
                instructions.insert(
                    instructions.index(definition_instruction) + 1, store_instruction
                )

        return instructions

    def _maybe_remove_from_list(self, list: List[T], element: T):
        if element in list:
            list.remove(element)
