"""
Hosts a simple HTTP server that can be used as Input node.
"""
import http.server
from typing import Any, Optional

from PyQt6.QtWidgets import QTextEdit
from promptflow.src.dialogues.node_options import NodeOptions

from promptflow.src.nodes.node_base import NodeBase


class Handler(http.server.BaseHTTPRequestHandler):
    """
    Override the default HTTP request handler to allow POST requests.
    """

    def do_POST(self):
        self.send_response(200)
        self.end_headers()

        # get data from request
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        self.server.data = post_data.decode("utf-8")


class ServerInputNode(NodeBase):
    """
    Blocking node that waits for a POST request to the specified port.
    """

    host: str = ""
    port: str = "8000"
    options_popup: Optional[NodeOptions]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = kwargs.get("host", "")
        self.port = kwargs.get("port", "8000")

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        with http.server.HTTPServer((self.host, int(self.port)), Handler) as httpd:
            httpd.handle_request()
            return httpd.data

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas, {"host": self.host, "port": self.port}
        )
        self.canvas.wait_window(self.options_popup)
        if self.options_popup.cancelled:
            return
        self.port = self.options_popup.result["port"]
        self.host = self.options_popup.result["host"]
