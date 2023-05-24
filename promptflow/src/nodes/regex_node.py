"""
Nodes that handle regular expressions and parsing text, usually 
from LLM output (but not always)
"""
import re
from typing import Any
from promptflow.src.dialogues.node_options import NodeOptions
from promptflow.src.nodes.node_base import NodeBase
from PyQt6.QtWidgets import QTextEdit


class RegexNode(NodeBase):
    """
    Node that handles regular expressions
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )
        self.regex = kwargs.get("regex", "")
        self.regex_item = self.canvas.create_text(
            self.center_x,
            self.center_y + 30,
            text=self.regex,
            font=("Arial", 10),
            fill="black",
            width=self.size_px * 2,
            justify="center",
        )
        self.items.append(self.regex_item)
        self.bind_drag()
        self.bind_mouseover()

        self.options_popup = None

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        """
        Runs the regex on the state
        """
        self.logger.info("Regex node %s has state %s", self.label, state)
        search = re.search(self.regex, state.result)
        if search is None:
            return ""
        return search.group(0)

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "regex": self.regex,
            },
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        if self.options_popup.cancelled:
            return
        self.regex = result["regex"]
        self.canvas.itemconfig(self.regex_item, text=self.regex)


class TagNode(NodeBase):
    """
    Gets the text in-between two tags
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_tag = kwargs.get("start_tag", "")
        self.end_tag = kwargs.get("end_tag", "")
        self.tags_item = self.canvas.create_text(
            self.center_x,
            self.center_y + 30,
            text=f"{self.start_tag}...{self.end_tag}",
            font=("Arial", 10),
            fill="black",
            width=self.size_px * 2,
            justify="center",
        )
        self.items.append(self.tags_item)
        self.canvas.tag_bind(self.tags_item, "<Double-Button-1>", self.edit_options)
        self.bind_drag()
        self.bind_mouseover()

        self.options_popup = None

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        """
        Extracts the text in-between the start and end tags from the state
        """
        self.logger.info("Tag node %s has state %s", self.label, state)
        content = state.result
        start_index = content.find(self.start_tag)
        end_index = content.find(self.end_tag, start_index)

        if start_index == -1 or end_index == -1:
            return ""

        start_index += len(self.start_tag)
        return content[start_index:end_index]

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "start_tag": self.start_tag,
                "end_tag": self.end_tag,
            },
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        if self.options_popup.cancelled:
            return
        self.start_tag = result["start_tag"]
        self.end_tag = result["end_tag"]
        self.canvas.itemconfig(
            self.tags_item, text=f"{self.start_tag}...{self.end_tag}"
        )
