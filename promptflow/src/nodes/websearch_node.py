"""
Nodes for querying the web.
"""

from abc import ABC
import os
from PyQt6.QtWidgets import QTextEdit
from typing import Any
from promptflow.src.nodes.node_base import NodeBase
from serpapi import GoogleSearch


class WebSearchNode(NodeBase, ABC):
    """
    Node that makes a web search.
    """


class SerpApiNode(WebSearchNode):
    """
    Query Google using the SerpApi.
    """

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        searchParams = {
            "engine": "google",
            "q": str(state.result),
            "location": "Austin, Texas, United States",
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
            "api_key": os.environ["SERP_API_KEY"],
        }
        search = GoogleSearch(searchParams)
        results = search.get_dict()["organic_results"]
        return str(results)
