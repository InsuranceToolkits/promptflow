"""
Holds text which gets formatted with state data
"""
from typing import TYPE_CHECKING, Any, Optional

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

    def run_subclass(self, before_result: Any, state) -> str:
        """
        Formats TextData with state data
        """
        prompt = self.prompt.text.format(state=state)
        state.result = prompt
        return prompt

    def serialize(self) -> dict:
        return super().serialize() | {
            "prompt": self.prompt.serialize(),
        }

    def get_options(self) -> dict[str, Any]:
        base_options = super().get_options()
        base_options["options"]["prompt"] = self.prompt.serialize()
        return base_options

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
