from typing import List, Dict

from dataclasses import dataclass

from activation_records.temp import Temp
from instruction_selection.assembly import Move
from liveness_analysis.flow_graph import AssemblerInformation
from liveness_analysis.graph import Graph


@dataclass
class LivenessResults:
    interference_graph: Graph[Temp]
    temporary_to_moves: Dict[Temp, List[Move]]
    move_instructions: List[Move]


def liveness(
        flow_graph: Graph[AssemblerInformation],
) -> LivenessResults:
    interference_graph = Graph[Temp]()
    move_instructions = []

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
        # Compute live_in and live_out sets
        if flow_node.information.is_move():
            if len(flow_node.information.definitions) == 1:
                move_destination = list(flow_node.information.definitions)[0]
                move_source = (
                    list(flow_node.information.uses)[0]
                    if len(flow_node.information.uses) == 1
                    else None
                )
                if move_source is not None:
                    temporary_to_moves[move_source].append(
                        flow_node.information.instruction
                    )
                    temporary_to_moves[move_destination].append(
                        flow_node.information.instruction
                    )
                    move_instructions.append(flow_node.information.instruction)
                for live_out_temporary in flow_node.information.live_out:
                    if live_out_temporary != move_source:
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
                    interference_graph.add_edge(
                        temporary_to_node[defined_temporary],
                        temporary_to_node[live_out_temporary],
                    )
                    interference_graph.add_edge(
                        temporary_to_node[live_out_temporary],
                        temporary_to_node[defined_temporary],
                    )

    return LivenessResults(interference_graph, temporary_to_moves, move_instructions)
