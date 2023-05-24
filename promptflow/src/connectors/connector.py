"""
This module contains the Connector class, which represents a connection
between two nodes in the flowchart.
"""
import math
import logging
from typing import Optional, Tuple
from PyQt6.QtGui import QPixmap

from promptflow.src.nodes.start_node import StartNode
from promptflow.src.serializable import Serializable
from promptflow.src.nodes.node_base import NodeBase
from promptflow.src.dialogues.code_input import CodeInput
from promptflow.src.text_data import TextData
from promptflow.src.themes import monokai

DEFAULT_COND_TEMPLATE = """def main(state):
\treturn True
"""

DEFAULT_COND_NAME = "Untitled.py"


class Connector(Serializable):
    """
    A connection between two nodes in the flowchart.
    """

    def __init__(
        self,
        canvas: QPixmap,
        node1: NodeBase,
        node2: NodeBase,
        condition: Optional[TextData | dict] = None,
    ):
        self.canvas = canvas
        self.node1 = node1
        self.node2 = node2
        self.flowchart = node1.flowchart
        points = self.get_points()
        self.item = canvas.create_line(
            points,  # type: ignore
            fill="black",
            width=2,
            tags="connector",
            arrow=tk.LAST,
            smooth=True,
        )
        node1.output_connectors.append(self)
        node2.input_connectors.append(self)
        self.logger = logging.getLogger(__name__)
        # each connector has a branching condition
        if not condition:
            condition = TextData(
                DEFAULT_COND_NAME, DEFAULT_COND_TEMPLATE, self.flowchart
            )
        if isinstance(condition, dict):
            condition = TextData.deserialize(condition, self.flowchart)
        if condition.text == "":
            condition.text = DEFAULT_COND_TEMPLATE
        self.condition: TextData = condition
        self.condition_label: Optional[int] = None
        self.filled_box: Optional[int] = self.create_condition_label()
        self.text_window: Optional[CodeInput] = None
        self.canvas.tag_bind(self.item, "<Button-3>", self.delete)
        self.canvas.tag_bind(self.item, "<Double-Button-1>", self.edit_condition)
        self.canvas.tag_bind(self.item, "<Button-1>", self.select)
        self.canvas.tag_bind(
            self.item, "<Enter>", lambda _: self.canvas.configure(cursor="hand2")
        )
        self.canvas.tag_bind(
            self.item, "<Leave>", lambda _: self.canvas.configure(cursor="arrow")
        )

    @property
    def label(self) -> str:
        return self.condition.label

    def get_points(self) -> tuple[float, ...]:
        """Return the coordinates of the top-left and bottom-right corners of the bounding box of the connector."""
        (center_x1, center_y1), (center_x2, center_y2) = self.get_sides()
        if self.detect_cycle() or isinstance(self.node2, StartNode):
            points = self.arc_line(center_x1, center_y1, center_x2, center_y2)
        else:
            points = center_x1, center_y1, center_x2, center_y2
        return points

    @classmethod
    def deserialize(
        cls, canvas: QPixmap, node1: NodeBase, node2: NodeBase, condition: TextData
    ):
        return cls(canvas, node1, node2, condition)

    def update(self):
        """
        Update the connector's position based on the position of the nodes it connects.
        """
        points = self.get_points()
        self.canvas.coords(self.item, points)
        if self.condition_label and self.filled_box:
            self.canvas.coords(
                self.condition_label,
                points[0] + (points[2] - points[0]) / 2,
                points[1] + (points[3] - points[1]) / 2,
            )
            self.canvas.coords(self.filled_box, self.canvas.bbox(self.condition_label))

    def serialize(self):
        return {
            "node1": self.node1.id,
            "node2": self.node2.id,
            "condition": self.condition.serialize(),
        }

    def delete(self, *args):
        """
        Remove the connector from the flowchart, both from the canvas and from the flowchart's list of connectors.
        """
        if self in self.node1.flowchart.connectors:
            self.node1.flowchart.connectors.remove(self)
        self.node1.output_connectors.remove(self)
        self.node2.input_connectors.remove(self)
        self.canvas.delete(self.item)
        if self.condition_label and self.filled_box:
            self.canvas.delete(self.condition_label)
            self.canvas.delete(self.filled_box)

    def edit_condition(self, _):
        """
        Bring up the text input window to edit the connector's condition.
        """

        self.text_window = CodeInput(self.canvas, self.flowchart, self.condition)
        self.text_window.set_callback(self.update_condition)

    def select(self, _):
        """
        Select the connector.
        """
        self.flowchart.selected_element = self

    def update_condition(self):
        """
        Update the connector's condition with the text in the text input window.
        """
        if self.text_window is None:
            self.logger.warning("Text window is None")
            return
        if self.condition_label and self.filled_box:
            self.canvas.delete(self.condition_label)
            self.canvas.delete(self.filled_box)
        self.condition = self.text_window.get_text()
        self.filled_box = self.create_condition_label()
        self.text_window.destroy()

    def get_sides(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Shortest distance between two nodes with arbitrary shapes
        """
        # get the coordinates of the two nodes
        x1, y1, x2, y2 = self.canvas.bbox(self.node1.item)
        x3, y3, x4, y4 = self.canvas.bbox(self.node2.item)
        # find the center of each node
        center_x1, center_y1 = (x1 + x2) / 2, (y1 + y2) / 2
        center_x2, center_y2 = (x3 + x4) / 2, (y3 + y4) / 2
        # find the angle between the two centers
        angle = math.atan2(center_y2 - center_y1, center_x2 - center_x1)
        # find the coordinates of the sides of the nodes
        # by moving the centers away from each other
        # by half the width and height of the nodes
        side_x1 = center_x1 + math.cos(angle) * (x2 - x1) / 2
        side_y1 = center_y1 + math.sin(angle) * (y2 - y1) / 2
        side_x2 = center_x2 - math.cos(angle) * (x4 - x3) / 2
        side_y2 = center_y2 - math.sin(angle) * (y4 - y3) / 2
        return (side_x1, side_y1), (side_x2, side_y2)

    def create_condition_label(self) -> Optional[int]:
        """
        Handles drawing the connector's condition label.
        """
        if is_condition_default(self.condition):
            return None
        points = self.get_points()
        self.condition_label = self.canvas.create_text(
            points[0] + (points[2] - points[0]) / 2,
            points[1] + (points[3] - points[1]) / 2,
            text=self.condition.label,
            tags="connector_label",
            fill="black",
        )
        # draw filled box behind text
        filled_box = self.canvas.create_rectangle(
            self.canvas.bbox(self.condition_label), fill=monokai.WHITE
        )
        self.canvas.tag_lower(filled_box, self.condition_label)
        self.canvas.tag_bind(self.condition_label, "<Button-3>", self.delete)
        self.canvas.tag_bind(
            self.condition_label, "<Double-Button-1>", self.edit_condition
        )
        self.canvas.tag_bind(filled_box, "<Double-Button-1>", self.edit_condition)
        self.canvas.tag_bind(self.condition_label, "<Button-1>", self.select)
        self.canvas.tag_bind(filled_box, "<Enter>", self.on_mouseover)
        self.canvas.tag_bind(self.condition_label, "<Enter>", self.on_mouseover)
        self.canvas.tag_bind(filled_box, "<Leave>", self.on_mouseleave)
        self.canvas.tag_bind(self.condition_label, "<Leave>", self.on_mouseleave)
        return filled_box

    def on_mouseover(self, _):
        """
        Shade the connector's condition label when the mouse hovers over it.
        """
        shade = 0.2
        cur_tuple = self.canvas.itemcget(self.filled_box, "fill")
        cur_tuple = tuple(int(cur_tuple[i : i + 2], 16) for i in (1, 3, 5))
        color = "#" + "".join(
            [hex(int(cur_tuple[i] * (1 - shade)))[2:] for i in range(3)]
        )
        self.canvas.itemconfig(self.filled_box, fill=color)
        # make cursor a hand
        self.canvas.configure(cursor="hand2")

    def on_mouseleave(self, _):
        """
        Restore the connector's condition label when the mouse leaves it.
        """
        self.canvas.itemconfig(self.filled_box, fill=monokai.WHITE)
        self.canvas.configure(cursor="arrow")

    def arc_line(
        self, x1: float, y1: float, x2: float, y2: float
    ) -> Tuple[float, float, float, float, float, float]:
        """Return points for a curved line between two points"""
        # find the midpoint between the two points
        x3 = (x1 + x2) / 2 + (y2 - y1) / 2
        y3 = (y1 + y2) / 2 + (x1 - x2) / 2
        return x1, y1, x3, y3, x2, y2

    def detect_cycle(self) -> bool:
        """
        Check if the node connects to itself or to a child of itself
        """
        if self.node1 == self.node2:
            return True
        if self.node1 in self.node2.get_children():
            return True
        return False


def is_condition_default(condition: TextData) -> bool:
    """
    Check if a condition is the default condition.
    """
    return (
        condition.label == DEFAULT_COND_NAME and condition.text == DEFAULT_COND_TEMPLATE
    )
