"""
Nodes for performing tests on the model.
"""
import code
from PyQt6.QtWidgets import QTextEdit
from typing import TYPE_CHECKING, Optional, Any
from promptflow.src.dialogues.node_options import NodeOptions
from promptflow.src.dialogues.text_input import TextInput

from promptflow.src.state import State
from promptflow.src.nodes.node_base import NodeBase
from promptflow.src.text_data import TextData
from promptflow.src.themes import monokai

if TYPE_CHECKING:
    from promptflow.src.flowchart import Flowchart


class AssertNode(NodeBase):
    """
    Runs an assertion on the result of the previous node
    """

    node_color = monokai.COMMENTS

    def __init__(
        self,
        flowchart: "Flowchart",
        center_x: float,
        center_y: float,
        label: str,
        assertion: Optional[TextData] = None,
        **kwargs,
    ):
        super().__init__(flowchart, center_x, center_y, label, **kwargs)
        if assertion is None:
            assertion = TextData("Assertion", "True", self.flowchart)
        self.assertion = assertion
        self.options_popup: Optional[NodeOptions] = None

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        assert eval(self.assertion.text, globals(), state.snapshot), "Assertion failed"
        return state.result

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas, {"Assertion": self.assertion.text}
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        # check if cancel
        if self.options_popup.cancelled:
            return
        self.assertion.text = result["Assertion"]


class LoggingNode(NodeBase):
    """
    Logs user-defined string to the console.
    """

    text_window: Optional[TextInput] = None

    def __init__(
        self,
        flowchart: "Flowchart",
        center_x: float,
        center_y: float,
        label: str,
        debug_str: Optional[TextData] = None,
        **kwargs,
    ):
        super().__init__(flowchart, center_x, center_y, label, **kwargs)
        if debug_str is None:
            debug_str = TextData("Debug String", "{state.result}", self.flowchart)
        self.debug_str = debug_str
        self.canvas.tag_bind(self.item, "<Double-Button-1>", self.edit_string)

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        debug_str = self.debug_str.text.format(state=state)
        self.logger.info(debug_str)
        return state.result  # return the result of the previous node

    def edit_string(self, event):
        self.text_window = TextInput(self.canvas, self.flowchart, self.debug_str)
        self.text_window.set_callback(self.save_prompt)

    def save_prompt(self, text):
        self.debug_str.text = text
        self.text_window.destroy()
        self.text_window = None


class InterpreterNode(NodeBase):
    """
    Starts an interactive Python interpreter
    """

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        code.interact(local=locals())
        return state.result
