"""
Interface for http requests
"""
from enum import Enum
import tkinter
from typing import Any, Callable
import json
import requests
from promptflow.src.dialogues.node_options import NodeOptions

from promptflow.src.nodes.node_base import NodeBase
from promptflow.src.state import State


class RequestType(Enum):
    """
    Types of http requests- for dropdown
    """

    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"


request_functions: dict[str, Callable[[Any], requests.Response]] = {
    RequestType.GET.value: requests.get,
    RequestType.POST.value: requests.post,
    RequestType.PUT.value: requests.put,
    RequestType.DELETE.value: requests.delete,
}


class HttpNode(NodeBase):
    """
    Makes a http request
    """

    url: str
    request_type: str
    options_popup: NodeOptions

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )
        self.url = kwargs.get("url", "")
        self.request_type = kwargs.get("request_type", RequestType.GET.value)
        self.options_popup: NodeOptions = None
        self.request_type_item = self.canvas.create_text(
            self.center_x,
            self.center_y + 30,
            text=self.request_type.upper(),
            font=("Arial", 10),
            fill="black",
            width=self.size_px * 2,
            justify="center",
        )
        self.items.append(self.request_type_item)
        self.canvas.tag_bind(
            self.request_type_item, "<Double-Button-1>", self.edit_options
        )
        self.bind_drag()
        self.bind_mouseover()

    def run_subclass(
        self, before_result: Any, state, console: tkinter.scrolledtext.ScrolledText
    ) -> str:
        """
        Sends a http request
        """
        try:
            data = json.loads(state.result)
        except json.decoder.JSONDecodeError:
            return "Invalid JSON"
        response = request_functions[self.request_type](self.url, json=data)
        return response.text

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "url": self.url,
                "request_type": self.request_type,
            },
            {
                "request_type": [
                    RequestType.GET.value,
                    RequestType.POST.value,
                    RequestType.PUT.value,
                    RequestType.DELETE.value,
                ],
            },
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        # check if cancel
        if self.options_popup.cancelled:
            return
        self.url = result["url"]
        self.request_type = result["request_type"]
        self.canvas.itemconfig(self.request_type_item, text=self.request_type.upper())

    def serialize(self):
        return super().serialize() | {
            "url": self.url,
            "request_type": self.request_type,
        }


class JSONRequestNode(NodeBase):
    """
    Parses the URL out of the state.result and makes a http request
    """

    key: str = "url"
    request_type: str
    options_popup: NodeOptions

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )
        self.request_type = kwargs.get("request_type", RequestType.GET.value)
        self.key = kwargs.get("key", "url")
        self.options_popup: NodeOptions = None
        self.request_type_item = self.canvas.create_text(
            self.center_x,
            self.center_y + 30,
            text=self.request_type.upper(),
            font=("Arial", 10),
            fill="black",
            width=self.size_px * 2,
            justify="center",
        )
        self.items.append(self.request_type_item)
        self.canvas.tag_bind(
            self.request_type_item, "<Double-Button-1>", self.edit_options
        )
        self.bind_drag()
        self.bind_mouseover()

    def run_subclass(
        self,
        before_result: Any,
        state: State,
        console: tkinter.scrolledtext.ScrolledText,
    ) -> str:
        """
        Sends a http request
        """
        try:
            data = json.loads(state.result)
        except json.decoder.JSONDecodeError:
            return "Invalid JSON"
        response = request_functions[self.request_type](data[self.key], json=data)
        return response.text

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "key": self.key,
                "request_type": self.request_type,
            },
            {
                "request_type": [
                    RequestType.GET.value,
                    RequestType.POST.value,
                    RequestType.PUT.value,
                    RequestType.DELETE.value,
                ],
            },
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        # check if cancel
        if self.options_popup.cancelled:
            return
        self.key = result["key"]
        self.request_type = result["request_type"]
        self.canvas.itemconfig(self.request_type_item, text=self.request_type.upper())

    def serialize(self):
        return super().serialize() | {
            "key": self.key,
            "request_type": self.request_type,
        }
