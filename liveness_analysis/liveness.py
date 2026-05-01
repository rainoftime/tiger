"""Interference-graph construction from liveness-annotated assembly CFGs.

This module performs the second half of the classic liveness pipeline:

1. ``flow_graph.py`` computes ``live_in`` and ``live_out`` sets for each
   instruction.
2. This file converts those sets into an interference graph suitable for graph
   coloring and records move instructions separately for later coalescing.
"""

from typing import List, Dict

from dataclasses import dataclass

from activation_records.temp import Temp
from instruction_selection.assembly import Move
from liveness_analysis.flow_graph import AssemblerInformation
from liveness_analysis.graph import Graph


@dataclass
class LivenessResults:
    """Artifacts consumed by the graph-coloring allocator."""

    interference_graph: Graph[Temp]
    temporary_to_moves: Dict[Temp, List[Move]]
    move_instructions: List[Move]


def liveness(
        flow_graph: Graph[AssemblerInformation],
) -> LivenessResults:
    """Build the interference graph for the already-solved flow graph.

    Two temporaries interfere when they must hold different physical registers.
    The standard rule is: every temp defined by an instruction interferes with
    every temp live-out of that instruction.

    Move instructions receive special treatment. For ``mov a, b``, the source
    ``a`` is excluded from the interference edges added for ``b`` so the
    allocator has a chance to coalesce the copy away later.
    """
    interference_graph = Graph[Temp]()
    move_instructions = []

    # First discover every temp that participates in the procedure so the
    # interference graph has a node for each one.
    temporaries = set()
    for flow_node in flow_graph.get_nodes():
        temporaries = temporaries.union(
            flow_node.information.definitions, flow_node.information.uses
        )

    temporary_to_moves = {temporary: [] for temporary in temporaries}
    temporary_to_node = {
        temporary: interference_graph.add_node(temporary) for temporary in temporaries
    }

    for flow_node in flow_graph.get_nodes():
        if flow_node.information.is_move():
            if len(flow_node.information.definitions) == 1:
                move_destination = list(flow_node.information.definitions)[0]
                move_source = (
                    list(flow_node.information.uses)[0]
                    if len(flow_node.information.uses) == 1
                    else None
                )
                if move_source is not None:
                    # Record move-related temps so the allocator can try to
                    # merge them during the coalescing phase.
                    temporary_to_moves[move_source].append(
                        flow_node.information.instruction
                    )
                    temporary_to_moves[move_destination].append(
                        flow_node.information.instruction
                    )
                    move_instructions.append(flow_node.information.instruction)
                for live_out_temporary in flow_node.information.live_out:
                    if live_out_temporary != move_source:
                        # ``move_destination`` conflicts with every other temp
                        # still live after the move. The source is skipped so a
                        # future coalescing step may assign both temps the same
                        # register and eliminate the move.
                        interference_graph.add_edge(
                            temporary_to_node[move_destination],
                            temporary_to_node[live_out_temporary],
                        )
                        interference_graph.add_edge(
                            temporary_to_node[live_out_temporary],
                            temporary_to_node[move_destination],
                        )
        else:
            for defined_temporary in flow_node.information.definitions:
                for live_out_temporary in flow_node.information.live_out:
                    # The graph implementation is directed, but interference is
                    # conceptually undirected, so both directions are inserted.
                    interference_graph.add_edge(
                        temporary_to_node[defined_temporary],
                        temporary_to_node[live_out_temporary],
                    )
                    interference_graph.add_edge(
                        temporary_to_node[live_out_temporary],
                        temporary_to_node[defined_temporary],
                    )

    return LivenessResults(interference_graph, temporary_to_moves, move_instructions)
