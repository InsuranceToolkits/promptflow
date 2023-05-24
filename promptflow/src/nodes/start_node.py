"""
Special node that prompts the user for input
Also signals the start of the flowchart
"""
from typing import TYPE_CHECKING, Any
import uuid
from PyQt6.QtWidgets import QTextEdit, QMainWindow
from PyQt6.QtGui import QPainter
from promptflow.src.nodes.node_base import NodeBase
from promptflow.src.themes import monokai

if TYPE_CHECKING:
    from promptflow.src.flowchart import Flowchart


class StartNode(NodeBase):
    """
    First node in the flowchart
    """

    node_color = monokai.BLUE

    def __init__(
        self,
        flowchart: "Flowchart",
        center_x: float,
        center_y: float,
        label: str,
        root: QMainWindow,
        **kwargs,
    ):
        # make sure there is only one start node
        for node in flowchart.nodes:
            if isinstance(node, StartNode):
                raise ValueError("Only one start node is allowed")

        super().__init__(flowchart, center_x, center_y, label, root, **kwargs)

    @staticmethod
    def deserialize(flowchart: "Flowchart", data: dict):
        return StartNode(
            flowchart,
            data["center_x"],
            data["center_y"],
            data["label"],
            root=flowchart.root,
            id=data.get("id", str(uuid.uuid4())),
        )

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        return ""

    def draw_shape(self, x: int, y: int):
        painter = QPainter(self.canvas)
        return painter.drawEllipse(
            x - self.size_px,
            y - self.size_px,
            x + self.size_px,
            y + self.size_px,
        )


class InitNode(NodeBase):
    """
    Initialization node that is only run once at the beginning of the flowchart
    """

    node_color = monokai.ORANGE

    def __init__(
        self,
        flowchart: "Flowchart",
        center_x: float,
        center_y: float,
        label: str,
        root: QMainWindow,
        **kwargs,
    ):
        # make sure there is only one init node
        for node in flowchart.nodes:
            if isinstance(node, InitNode):
                raise ValueError("Only one init node is allowed")

        super().__init__(flowchart, center_x, center_y, label, root, **kwargs)
        self.run_once = False

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        if not self.run_once:
            self.run_once = True
            return ""
        else:
            return None

    def draw_shape(self, x: int, y: int):
        painter = QPainter(self.canvas)
        return painter.drawEllipse(
            x - self.size_px,
            y - self.size_px,
            x + self.size_px,
            y + self.size_px,
        )
