"""
Initialize environmental variables using .env
"""
import os
from typing import Any, Optional
from PyQt6.QtWidgets import QTextEdit

from dotenv import load_dotenv
from promptflow.src.dialogues.multi_file import MultiFileInput
from promptflow.src.dialogues.node_options import NodeOptions

from promptflow.src.nodes.node_base import NodeBase


class EnvNode(NodeBase):
    """
    Loads environmental variables from a .env file
    """

    filename: str = ".env"
    options_popup: Optional[MultiFileInput] = None

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.filename = kwargs.get("filename", ".env")

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        load_dotenv(self.filename)
        return state.result

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

    def serialize(self):
        return super().serialize() | {
            "filename": self.filename,
        }


class ManualEnvNode(NodeBase):
    """
    Manually set an environmental variable
    """

    key: str = ""
    val: str = ""
    options_popup: Optional[NodeOptions] = None

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.key = kwargs.get("key", "")
        self.val = kwargs.get("val", "")

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        os.environ[self.key] = self.val
        return state.result

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "key": self.key,
                "value": self.val,
            },
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        if self.options_popup.cancelled:
            return
        self.key = result["key"]
        self.val = result["value"]

    def serialize(self):
        return super().serialize() | {
            "key": self.key,
            "val": self.val,
        }
