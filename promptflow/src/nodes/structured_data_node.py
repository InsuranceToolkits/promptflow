"""
Nodes for handling structured data.
"""
from abc import ABC, abstractmethod
import ast
import json
from typing import Any
from PyQt6.QtWidgets import QTextEdit
import jsonschema
from promptflow.src.dialogues.text_input import TextInput
from promptflow.src.nodes.node_base import NodeBase
from promptflow.src.state import State
from promptflow.src.text_data import TextData


class StructuredDataNode(NodeBase, ABC):
    """
    Base class for nodes that handle structured data.
    """

    schema = None
    text_input = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.schema = kwargs.get("schema", None)

    @abstractmethod
    def validate(self, data):
        """
        Validate the data.
        """

    def run_subclass(
        self, before_result: Any, state: State, console: QTextEdit
    ) -> str:
        validation: str = self.validate(state.result)
        return validation

    def serialize(self):
        return super().serialize() | {"schema": self.schema}


class JsonNode(StructuredDataNode):
    """
    Node that validates JSON into a python dictionary.
    """

    def edit_options(self, event):
        """
        Allow user to edit the schema.
        """
        # create a text input dialogue
        text_data = TextData(
            "Schema", json.dumps(self.schema, indent=4), self.flowchart
        )
        self.text_input = TextInput(self.canvas, self.flowchart, text_data)
        self.text_input.set_callback(self.save_options)

    def validate(self, data):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return "Invalid JSON"
        try:
            jsonschema.validate(data, self.schema)
        except jsonschema.ValidationError as e:
            return "Validation error: " + str(e)
        except jsonschema.SchemaError as e:
            return "Schema error: " + str(e)
        return data

    def save_options(self):
        """
        Save the schema.
        """
        self.schema = json.loads(self.text_input.get_text().text)
        self.text_input.destroy()
        self.text_input = None


class JsonerizerNode(NodeBase):
    """
    Node that converts a python dictionary into JSON.
    """

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        d: dict = ast.literal_eval(state.result)
        return json.dumps(d, indent=4)
