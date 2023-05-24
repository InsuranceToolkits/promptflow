"""
Handles long term memory storage and retrieval.
"""

from abc import ABC
import os
from uuid import uuid4
from typing import Any, Optional
from PyQt6.QtWidgets import QTextEdit

import pinecone
from InstructorEmbedding import INSTRUCTOR

from promptflow.src.nodes.node_base import NodeBase
from promptflow.src.dialogues.node_options import NodeOptions
from promptflow.src.state import State


class MemoryNode(NodeBase, ABC):
    pass


class PineconeNode(MemoryNode, ABC):
    """
    Handles data in Pinecone. Uses InstructorEmbedding to encode data.
    Dimensions: 768
    """

    index: Optional[str] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = kwargs.get("index", None)

    def embed(self, state: State) -> Any:
        instructor = INSTRUCTOR("hkunlp/instructor-large")
        embedding = instructor.encode(state.result)
        return embedding

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        pinecone.init(
            api_key=os.environ["PINECONE_API_KEY"],
            environment=os.environ["PINECONE_ENVIRONMENT"],
        )
        return state.result

    def edit_options(self, event):
        options_popup = NodeOptions(
            self.canvas,
            {
                "index": self.index,
            },
        )
        self.canvas.wait_window(options_popup)
        if options_popup.cancelled:
            return
        self.index = options_popup.result["index"]


class PineconeInsertNode(PineconeNode):
    """
    Inserts data into Pinecone
    """

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        super().run_subclass(before_result, state, console)
        if self.index is None:
            console.insert("end", "Index must be set")
            raise ValueError("Index must be set")
        index = pinecone.Index(self.index)
        embedding = self.embed(state)
        index.upsert([(uuid4(), embedding, {"text": state.result})])
        return state.result


class PineconeQueryNode(PineconeNode):
    """
    Queries data from Pinecone
    """

    k = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.k = kwargs.get("k", 1)

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        super().run_subclass(before_result, state, console)
        if self.index is None:
            console.insert("end", "Index must be set")
            raise ValueError("Index must be set")
        index = pinecone.Index(self.index)
        embedding = self.embed(state.result)
        results = index.query(embedding, k=self.k, include_metadata=True)
        console.insert("end", f"Results: {results}")
        result = ""
        for match in results["matches"]:
            result += f"{match['metadata']['text']}\n"
        return result

    def edit_options(self, event):
        options_popup = NodeOptions(
            self.canvas,
            {
                "index": self.index,
                "k": self.k,
            },
        )
        self.canvas.wait_window(options_popup)
        if options_popup.cancelled:
            return
        self.index = options_popup.result["index"]
        self.k = options_popup.result["k"]
