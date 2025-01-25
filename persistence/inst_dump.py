from graphviz import Digraph


def pretty_print_instructions(instructions, filename: str):
    dot = Digraph()

    def add_node(instruction, parent=None):
        node_id = str(id(instruction))
        label = str(instruction)
        dot.node(node_id, label)
        if parent:
            dot.edge(str(id(parent)), node_id)

    for instruction in instructions:
        add_node(instruction)
    dot.render(filename, format='dot', cleanup=True)


def pretty_print_instructions_after_selection(instructions, filename: str):
    pretty_print_instructions(instructions, filename)


def pretty_print_instructions_after_allocation(instructions, filename: str):
    pretty_print_instructions(instructions, filename)
