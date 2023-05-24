"""
Manages writing history to state
"""
from abc import ABC
from typing import TYPE_CHECKING, Any, Optional
from PyQt6.QtWidgets import QTextEdit
from promptflow.src.dialogues.history_editor import HistoryEditor, Role

from promptflow.src.dialogues.node_options import NodeOptions
from promptflow.src.nodes.node_base import NodeBase

from promptflow.src.state import State

if TYPE_CHECKING:
    from promptflow.src.flowchart import Flowchart

from promptflow.src.themes import monokai


class HistoryNode(NodeBase):
    """
    Injects history into state
    """

    node_color = monokai.PINK

    def __init__(
        self,
        flowchart: "Flowchart",
        center_x: float,
        center_y: float,
        label: str,
        **kwargs,
    ):
        super().__init__(
            flowchart,
            center_x,
            center_y,
            label,
            **kwargs,
        )
        self.role_var = tk.StringVar(value=kwargs.get("role", Role.USER.value))
        self.role_item = self.canvas.create_text(
            center_x,
            center_y + 30,
            text=self.role_var.get(),
            font=("Arial", 10),
            fill="black",
            width=self.size_px * 2,
            justify="center",
        )
        self.items.append(self.role_item)
        self.bind_drag()
        self.bind_mouseover()
        self.canvas.tag_bind(self.role_item, "<Double-Button-1>", self.edit_options)
        self.options_popup: Optional[NodeOptions] = None

    def run_subclass(
        self, before_result: Any, state: State, console: QTextEdit
    ) -> str:
        """
        Injects date into state
        """
        state.history.append({"role": self.role_var.get(), "content": state.result})
        return state.result

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "role": self.role_var.get(),
            },
            {
                "role": [Role.USER.value, Role.SYSTEM.value, Role.ASSISTANT.value],
            },
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        # check if cancel
        if self.options_popup.cancelled:
            return
        self.role_var.set(result["role"])
        self.canvas.itemconfig(self.role_item, text=self.role_var.get())

    def serialize(self):
        return super().serialize() | {
            "role": self.role_var.get(),
        }


class ManualHistoryNode(NodeBase):
    """
    Allows the user to specify a long history manually
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
        self.manual_history = kwargs.pop("manual_history", [])
        self.history_popup = None

    def edit_options(self, event):
        # show the history editor
        self.history_popup = HistoryEditor(self.canvas, self.manual_history)
        self.canvas.wait_window(self.history_popup)
        self.manual_history = self.history_popup.history

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        state.history.extend(self.manual_history)
        return state.result

    def serialize(self):
        return super().serialize() | {"manual_history": self.manual_history}


class HistoryWindow(NodeBase, ABC):
    """
    Stores messages in a list
    """

    node_color = monokai.BLUE

    def __init__(
        self,
        flowchart: "Flowchart",
        center_x: float,
        center_y: float,
        label: str,
        **kwargs,
    ):
        super().__init__(
            flowchart,
            center_x,
            center_y,
            label,
            **kwargs,
        )
        self.canvas.tag_bind(self.item, "<Double-Button-1>", self.edit_options)
        self.options_popup = None

    def apply_window(self, state: State) -> list[dict[str, str]]:
        """
        Update state history
        """
        state.history = state.history
        return state.history

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        history_string = "\n".join(
            [
                *[
                    f"{message['role']}: {message['content']}"
                    for message in self.apply_window(state)
                ],
            ]
        )
        return history_string


class WindowedHistoryNode(HistoryWindow):
    """
    Like MemoryNode, but only returns the last n messages
    """

    def __init__(
        self,
        flowchart: "Flowchart",
        center_x: float,
        center_y: float,
        label: str,
        window: int = 100,
        **kwargs,
    ):
        super().__init__(
            flowchart,
            center_x,
            center_y,
            label,
            **kwargs,
        )
        self.window = window

    def apply_window(self, state):
        state.history = state.history[-self.window :]
        return state.history

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {"window": self.window},
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        # check if cancel
        if self.options_popup.cancelled:
            return
        self.window = int(result["window"])

    def serialize(self):
        return super().serialize() | {"window": self.window}


class DynamicWindowedHistoryNode(HistoryWindow):
    """
    Given a string, will return the last n messages until the string is found
    """

    def __init__(
        self,
        flowchart: "Flowchart",
        center_x: float,
        center_y: float,
        label: str,
        target: str = "",
        **kwargs,
    ):
        super().__init__(
            flowchart,
            center_x,
            center_y,
            label,
            **kwargs,
        )
        self.target = target

    def apply_window(self, state: State) -> list[dict[str, str]]:
        """
        Update state history
        """
        history = state.history
        for i, message in enumerate(history):
            if eval(self.target, {}, message):
                history = history[i:]
                break
        return history

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {"target": self.target},
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        # check if cancel
        if self.options_popup.cancelled:
            return
        self.target = result["target"]

    def serialize(self):
        return super().serialize() | {"target": self.target}
