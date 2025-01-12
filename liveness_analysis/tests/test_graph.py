import unittest

from liveness_analysis.graph import Graph


class TestGraph(unittest.TestCase):
    def setUp(self):
        self.graph = Graph[int]()

    def test_add_node(self):
        for value in range(5):
            node = self.graph.add_node(value)
            self.assertEqual(value, node.information)

    def test_get_nodes(self):
        for value in range(5):
            self.graph.add_node(value)

        nodes = self.graph.get_nodes()

        self.assertEqual(len(nodes), 5)
        self.assertEqual(list(range(5)), [node.information for node in nodes])

    def test_node_successors(self):
        origin = self.graph.add_node(0)
        destination = self.graph.add_node(1)
        unrelated = self.graph.add_node(2)

        self.assertEqual(self.graph.node_successors(origin), [])

        self.graph.add_edge(origin, destination)

        self.assertIn(destination, self.graph.node_successors(origin))
        self.assertNotIn(unrelated, self.graph.node_successors(origin))

    def test_node_predecessors(self):
        origin = self.graph.add_node(0)
        destination = self.graph.add_node(1)
        unrelated = self.graph.add_node(2)

        self.assertEqual(self.graph.node_predecessors(origin), [])

        self.graph.add_edge(origin, destination)

        self.assertIn(origin, self.graph.node_predecessors(destination))
        self.assertNotIn(unrelated, self.graph.node_predecessors(destination))
