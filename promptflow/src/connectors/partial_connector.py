"""A connector that is being drawn by the user"""
import logging
from typing import TYPE_CHECKING, Optional

from promptflow.src.nodes.node_base import NodeBase
from promptflow.src.connectors.connector import Connector

if TYPE_CHECKING:
    from promptflow.src.flowchart import Flowchart


class PartialConnector:
    """
    A connector that is being drawn by the user
    Animates a line from the center of the node to the mouse position
    """

    def __init__(self, flowchart: "Flowchart", node: NodeBase):
        self.flowchart = flowchart
        self.logger = logging.getLogger(__name__)
        self.canvas = flowchart.canvas
        self.node = node
        x1, y1, x2, y2, *_ = self.canvas.coords(node.item)
        self.x = (x1 + x2) / 2
        self.y = (y1 + y2) / 2
        self.item = self.canvas.create_line(
            self.x, self.y, self.x, self.y, fill="black", width=2, tags="connector"
        )

    def update(self, event):
        """
        Move the line to the mouse position
        """
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.item, self.x, self.y, x, y)

    def finish(self, event):
        """
        Create a connector if the mouse is over a node
        """
        self.canvas.delete(self.item)
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        try:
            for node in self.flowchart.nodes:
                if node.item == self.canvas.find_overlapping(x, y, x, y)[0]:
                    if not self.check_exists(node):
                        self.flowchart.add_connector(
                            Connector(self.canvas, self.node, node)
                        )
                        break
        except IndexError:
            self.logger.debug("No node found at this position")
        self.canvas.unbind("<Button-1>")

    def delete(self, event):
        """Delete the line"""
        self.canvas.delete(self.item)

    def check_exists(self, node: NodeBase) -> bool:
        """
        Check if a connector already exists between source and given
        nodes
        """
        for connector in self.flowchart.connectors:
            if connector.node1 == self.node and connector.node2 == node:
                self.logger.debug("Connector already exists")
                return True
        return False
