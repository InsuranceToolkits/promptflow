"""
Holds text which gets formatted with state data
"""
from typing import TYPE_CHECKING, Any, Optional
from PyQt6.QtWidgets import QTextEdit
from promptflow.src.dialogues.text_input import TextInput
from promptflow.src.nodes.node_base import NodeBase
from promptflow.src.state import State

from promptflow.src.text_data import TextData
from promptflow.src.themes import monokai

if TYPE_CHECKING:
    from promptflow.src.flowchart import Flowchart


class PromptNode(NodeBase):
    """
    Formats TextData with state data
    """

    node_color = monokai.PURPLE

    def __init__(
        self,
        flowchart: "Flowchart",
        center_x: float,
        center_y: float,
        label: str,
        prompt: Optional[TextData | dict] = None,
        **kwargs,
    ):
        super().__init__(
            flowchart,
            center_x,
            center_y,
            label,
            **kwargs,
        )
        if prompt is None:
            prompt = TextData("Prompt", "", self.flowchart)
        if isinstance(prompt, dict):
            prompt = TextData.deserialize(prompt, self.flowchart)
        self.prompt = prompt
        self.prompt_item = self.canvas.create_text(
            center_x,
            center_y + 30,
            text=self.prompt.label,
            fill="black",
            width=self.size_px * 2,
            justify="center",
        )
        self.items.extend([self.prompt_item])
        self.canvas.tag_bind(self.prompt_item, "<Double-Button-1>", self.edit_options)

        self.text_window: Optional[TextInput] = None
        self.bind_drag()
        self.bind_mouseover()

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        """
        Formats TextData with state data
        """
        prompt = self.prompt.text.format(state=state)
        state.result = prompt
        return prompt

    def edit_options(self, _):
        """
        Create a text input window to edit the prompt.
        """
        self.text_window = TextInput(self.canvas, self.flowchart, self.prompt)
        self.text_window.set_callback(self.save_prompt)

    def save_prompt(self):
        """
        Write the prompt to the canvas.
        """
        if self.text_window is None:
            self.logger.warning("No text window to save")
            return
        self.prompt = self.text_window.get_text()
        self.canvas.itemconfig(self.prompt_item, text=self.prompt.label)
        self.text_window.destroy()

    def serialize(self) -> dict:
        return super().serialize() | {
            "prompt": self.prompt.serialize(),
        }

    @classmethod
    def deserialize(cls, flowchart: "Flowchart", data: dict) -> "PromptNode":
        return cls(
            flowchart,
            data["center_x"],
            data["center_y"],
            data["label"],
            prompt=data["prompt"],
            id=data["id"],
        )

    def cost(self, state: State):
        state.result = self.prompt.text
        return 0
