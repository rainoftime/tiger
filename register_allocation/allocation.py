"""
Graph Coloring Register Allocator for Tiger Compiler

This module implements graph coloring register allocation using the algorithm
described in "Modern Compiler Implementation in ML" by Andrew Appel.

The register allocator:
1. **Builds interference graph** from liveness information
2. **Colors the graph** using graph coloring heuristics
3. **Handles spills** when coloring fails (not enough registers)
4. **Coalesces** move instructions to eliminate unnecessary copies

Algorithm Overview:
- Simplify: Remove non-constrained temporaries and push on stack
- Coalesce: Merge move-related temporaries when safe
- Freeze: Freeze low-degree move-related temporaries
- Spill: Select spill candidates when no other options exist
- Select: Pop stack and assign colors (register mappings)

Key Data Structures:
- Interference Graph: Nodes represent temporaries, edges represent conflicts
- Worklists: Separate queues for different types of temporaries
- Coloring: Mapping from temporaries to physical registers
- Spilling: When not enough registers, some temporaries go to memory

Author: Tiger Compiler Project
"""

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
    """
    Result of register allocation process.

    Contains the final instruction sequence with register assignments
    and the mapping from temporary variables to physical registers.

    Attributes:
        instructions (List[Instruction]): Assembly instructions with registers assigned
        temp_to_register (Dict[Temp, Temp]): Mapping from temporaries to registers
    """
    instructions: List[Instruction]
    temp_to_register: Dict[Temp, Temp]


class RegisterAllocator:
    """
    Graph coloring register allocator for a single function frame.

    This class implements the complete register allocation algorithm for one function,
    including interference graph construction, graph coloring, and spill code generation.

    The allocator uses a worklist-based algorithm with four main phases:
    - Simplify: Remove easy-to-color nodes
    - Coalesce: Merge compatible move instructions
    - Freeze: Freeze low-degree move-related nodes
    - Spill: Select nodes to spill to memory when coloring fails

    Attributes:
        frame (Frame): The stack frame for the function being allocated
    """

    def __init__(self, frame: Frame):
        """
        Initialize register allocator for a specific function frame.

        Args:
            frame (Frame): Stack frame containing register and memory layout info
        """
        self.frame = frame

    def main(self, instructions: List[Instruction]) -> AllocationResult:
        """
        Perform complete register allocation for a function.

        This method runs the full register allocation algorithm:
        1. Initialize data structures (interference graph, worklists)
        2. Iteratively apply simplify/coalesce/freeze/spill until no work remains
        3. Assign colors (register mappings) to all temporaries
        4. If spills occurred, rewrite program and restart allocation

        Args:
            instructions (List[Instruction]): Assembly instructions to allocate

        Returns:
            AllocationResult: Final instructions with registers assigned and temp->register mapping
        """
        # Initialize all data structures from liveness analysis
        self._initialize_data_structures(instructions)

        # Main allocation loop: continue until all worklists are empty
        while (
                self.simplify_worklist
                or self.worklist_moves
                or self.freeze_worklist
                or self.spill_worklist
        ):
            if self.simplify_worklist:
                self._simplify()      # Remove non-constrained temporaries
            elif self.worklist_moves:
                self._coalesce()     # Merge compatible moves
            elif self.freeze_worklist:
                self._freeze()       # Freeze low-degree move-related nodes
            elif self.spill_worklist:
                self._select_spill() # Select spill candidates

        # Assign final register mappings (colors) to all temporaries
        self._assign_colors()

        # If any temporaries were spilled to memory, rewrite program and retry
        if self.spilled_nodes:
            new_instructions = self._rewrite_program(instructions)
            return self.main(new_instructions)  # Recursive retry after spilling

        # Success: return final allocation result
        return AllocationResult(instructions, self.color)

    def _initialize_data_structures(self, instructions: List[Instruction]):
        """
        Initialize all data structures needed for register allocation.

        This method builds the foundation for the allocation algorithm by:
        1. Constructing control flow graph from assembly instructions
        2. Computing liveness information and interference graph
        3. Categorizing temporaries into different worklists
        4. Setting up adjacency and coloring data structures

        Args:
            instructions (List[Instruction]): Assembly instructions to analyze
        """
        # Build control flow graph and extract use/def information
        flow_graph_results = assembler_flow_graph(instructions)
        self.temp_uses: Dict[Temp, List[Instruction]] = flow_graph_results.temp_uses
        self.temp_definitions: Dict[Temp, List[Instruction]] = flow_graph_results.temp_definitions

        # Compute liveness information and build interference graph
        liveness_results = liveness(flow_graph_results.flow_graph)
        all_temporaries = [
            node.information for node in liveness_results.interference_graph.get_nodes()
        ]

        # Separate precolored (machine register) temporaries from user temporaries
        self.precolored: List[Temp] = list(TempMap.register_to_temp.values())
        self.color_amount: int = len(self.precolored)  # Number of available registers
        self.initial: List[Temp] = [
            temporary
            for temporary in all_temporaries
            if temporary not in self.precolored  # User-defined temporaries only
        ]

        # Initialize worklists for different types of temporaries
        self.simplify_worklist: List[Temp] = []  # Low-degree non-move-related temps
        self.freeze_worklist: List[Temp] = []    # Low-degree move-related temps
        self.spill_worklist: List[Temp] = []     # High-degree temps (spill candidates)
        self.spilled_nodes: List[Temp] = []      # Temporaries that were spilled
        self.coalesced_nodes: List[Temp] = []    # Temporaries that were coalesced
        self.colored_nodes: List[Temp] = []      # Temporaries with assigned colors
        self.select_stack: List[Temp] = []       # Stack for coloring algorithm

        # Initialize move-related data structures
        self.coalesced_moves: List[Move] = []    # Successfully coalesced moves
        self.constrained_moves: List[Move] = []  # Moves that couldn't be coalesced
        self.frozen_moves: List[Move] = []       # Frozen moves (no longer considered)
        self.worklist_moves: List[Move] = liveness_results.move_instructions  # Moves to consider
        self.active_moves: List[Move] = []       # Moves involving colored temps

        # Set up graph structures from interference analysis
        self._initialize_adjacency_structures(liveness_results.interference_graph)
        self.move_list: Dict[Temp, List[Move]] = liveness_results.temporary_to_moves

        # Initialize coloring and aliasing mappings
        self.alias: Dict[Temp, Temp] = {}  # Maps coalesced temps to their canonical temp
        self.color: Dict[Temp, Temp] = {
            temporary: temporary for temporary in self.precolored  # Precolored temps map to themselves
        }

        # Populate initial worklists based on temporary properties
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
        """Georage's conservative coalesceable algorithm"""
        return (
                self.node_degree[node] < self.color_amount
                or node in self.precolored
                or (node, precolored_node) in self.adjacencies
        )

    def _conservative_coalesceable(self, nodes: Set[Temp]) -> bool:
        significant_node_count = 0
        """Briggs's conservative coalesceable algorithm"""
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
