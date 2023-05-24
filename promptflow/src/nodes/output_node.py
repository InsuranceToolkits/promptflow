"""
Nodes that output data to the user, such as text or files
"""

import json
from typing import Any
from PyQt6.QtWidgets import QTextEdit
from promptflow.src.dialogues.multi_file import MultiFileInput
from promptflow.src.dialogues.node_options import NodeOptions

from promptflow.src.nodes.node_base import NodeBase


class FileOutput(NodeBase):
    """
    Outputs data to a file
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = kwargs.get("filename", "")
        self.mode = kwargs.get("mode", "w")

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "filename": self.filename,
                "mode": self.mode,
            },
            dropdown_options={"mode": ["w", "a"]},
            file_options={"filename": {}},
        )
        self.canvas.wait_window(self.options_popup)
        if self.options_popup.cancelled:
            return
        self.filename = self.options_popup.result["filename"]

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ):
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(state.result)
        return state.result


class JSONFileOutput(NodeBase):
    """
    Outputs data to a file location parsed from the state.result
    """

    filename_key: str = "filename"
    data_key: str = "data"
    options_popup: NodeOptions

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.filename_key = kwargs.get("filename_key", "")
        self.data_key = kwargs.get("data_key", "")

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "filename_key": self.filename_key,
                "data_key": self.data_key,
            },
        )
        self.canvas.wait_window(self.options_popup)
        if self.options_popup.cancelled:
            return
        self.filename_key = self.options_popup.result["filename_key"]
        self.data_key = self.options_popup.result["data_key"]

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ):
        data = json.loads(state.result)
        filename = data[self.filename_key]
        with open(filename, "w", encoding="utf-8") as f:
            f.write(data[self.data_key])
        return state.result

    def serialize(self) -> dict[str, Any]:
        return super().serialize() | {
            "filename_key": self.filename_key,
            "data_key": self.data_key,
        }
