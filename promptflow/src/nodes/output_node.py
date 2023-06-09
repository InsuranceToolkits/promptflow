"""
Nodes that output data to the user, such as text or files
"""

import json
import customtkinter
from typing import Any
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
        self, before_result: Any, state, console: customtkinter.CTkTextbox
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
    mode: str = "w"
    options_popup: NodeOptions

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.filename_key = kwargs.get("filename_key", "")
        self.data_key = kwargs.get("data_key", "")
        self.mode = kwargs.get("mode", "w")

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "filename_key": self.filename_key,
                "data_key": self.data_key,
                "mode": self.mode,
            },
            dropdown_options={"mode": ["w", "a"]},
        )
        self.canvas.wait_window(self.options_popup)
        if self.options_popup.cancelled:
            return
        self.filename_key = self.options_popup.result["filename_key"]
        self.data_key = self.options_popup.result["data_key"]
        self.mode = self.options_popup.result["mode"]

    def run_subclass(
        self, before_result: Any, state, console: customtkinter.CTkTextbox
    ):
        data = json.loads(state.result)
        filename = data[self.filename_key]
        with open(filename, self.mode, encoding="utf-8") as f:
            f.write(data[self.data_key])
        return state.result

    def serialize(self) -> dict[str, Any]:
        return super().serialize() | {
            "filename_key": self.filename_key,
            "data_key": self.data_key,
            "mode": self.mode,
        }
