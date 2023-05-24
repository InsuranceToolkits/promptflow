"""
Nodes that get run time input from the user
"""
import json
from typing import Any, Optional
from PyQt6.QtWidgets import QTextEdit
from promptflow.src.dialogues.multi_file import MultiFileInput
from promptflow.src.dialogues.node_options import NodeOptions

from promptflow.src.nodes.node_base import NodeBase


class InputNode(NodeBase):
    """
    Node that prompts the user for input
    """

    def before(self, state, console):
        dialog = customtkinter.CTkInputDialog(
            text="Enter a value for this input:", title=self.label
        )
        dialog.grab_set()
        return {"input": dialog.get_input()}

    def run_subclass(self, before_result, state, console):
        if before_result["input"] == "":
            return None
        return before_result["input"]


class FileInput(NodeBase):
    """
    Reads a file and returns its contents
    """

    options_popup: Optional[MultiFileInput] = None
    filename: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = kwargs.get("filename", "")

    def edit_options(self, event):
        self.options_popup = MultiFileInput(
            self.canvas,
            {
                "filename": self.filename,
            },
        )
        self.canvas.wait_window(self.options_popup)
        if self.options_popup.cancelled:
            return
        self.filename = self.options_popup.result["filename"]

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        with open(self.filename, "r", encoding="utf-8") as f:
            return f.read()

    def serialize(self) -> dict[str, Any]:
        return super().serialize() | {"filename": self.filename}


class JSONFileInput(NodeBase):
    """
    Parses a specific input from the state.result and reads a file and returns its contents
    """

    key: str = "filename"
    options_popup: Optional[NodeOptions] = None

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.key = kwargs.get("key", "")

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "key": self.key,
            },
        )
        self.canvas.wait_window(self.options_popup)
        if self.options_popup.cancelled:
            return
        self.key = self.options_popup.result["key"]

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        data = json.loads(state.result)
        with open(data[self.key], "r", encoding="utf-8") as f:
            return f.read()

    def serialize(self) -> dict[str, Any]:
        return super().serialize() | {"key": self.key}
