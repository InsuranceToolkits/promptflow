import random
from PyQt6.QtWidgets import QTextEdit
from promptflow.src.dialogues.node_options import NodeOptions
from promptflow.src.nodes.node_base import NodeBase
from promptflow.src.themes import monokai

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from promptflow.src.flowchart import Flowchart


class RandomNode(NodeBase):
    """
    Injects a random number (min-max) into state
    """

    node_color = monokai.PINK
    min: int = 0
    max: int = 100
    option_popup: Optional[NodeOptions] = None

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        r = random.randint(self.min, self.max)
        return str(r)

    def edit_options(self, event):
        self.option_popup = NodeOptions(
            self.canvas,
            {
                "min": self.min,
                "max": self.max,
            },
        )
        self.canvas.wait_window(self.option_popup)
        result = self.option_popup.result
        if self.option_popup.cancelled:
            return
        self.min = int(result["min"])
        self.max = int(result["max"])
