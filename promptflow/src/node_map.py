"""
Maps node names to node classes
"""
from typing import Dict, Type
from promptflow.src.nodes.embedding_node import (
    EmbeddingsIngestNode,
)
from promptflow.src.nodes.node_base import NodeBase
from promptflow.src.nodes.start_node import InitNode, StartNode
from promptflow.src.nodes.input_node import InputNode, FileInput, JSONFileInput
from promptflow.src.nodes.func_node import FuncNode
from promptflow.src.nodes.llm_node import OpenAINode, ClaudeNode, GoogleVertexNode
from promptflow.src.nodes.date_node import DateNode
from promptflow.src.nodes.random_number import RandomNode
from promptflow.src.nodes.history_node import (
    HistoryNode,
    ManualHistoryNode,
    HistoryWindow,
    WindowedHistoryNode,
    DynamicWindowedHistoryNode,
)
from promptflow.src.nodes.dummy_llm_node import DummyNode
from promptflow.src.nodes.prompt_node import PromptNode
from promptflow.src.nodes.embedding_node import (
    EmbeddingInNode,
    EmbeddingQueryNode,
    EmbeddingsIngestNode,
)
from promptflow.src.nodes.test_nodes import AssertNode, LoggingNode, InterpreterNode
from promptflow.src.nodes.env_node import EnvNode, ManualEnvNode
from promptflow.src.nodes.audio_node import WhispersNode, ElevenLabsNode
from promptflow.src.nodes.db_node import PGQueryNode, SQLiteQueryNode, PGGenerateNode
from promptflow.src.nodes.structured_data_node import JsonNode, JsonerizerNode
from promptflow.src.nodes.websearch_node import SerpApiNode, GoogleSearchNode
from promptflow.src.nodes.output_node import FileOutput, JSONFileOutput
from promptflow.src.nodes.http_node import HttpNode, JSONRequestNode, ScrapeNode
from promptflow.src.nodes.server_node import ServerInputNode
from promptflow.src.nodes.memory_node import PineconeInsertNode, PineconeQueryNode
from promptflow.src.nodes.image_node import (
    DallENode,
    CaptionNode,
    OpenImageFile,
    JSONImageFile,
    SaveImageNode,
)

node_map: Dict[str, Type[NodeBase]] = {
    "InitNode": InitNode,
    "StartNode": StartNode,
    "InputNode": InputNode,
    "FileInput": FileInput,
    "JSONFileInput": JSONFileInput,
    "FuncNode": FuncNode,
    "OpenAINode": OpenAINode,
    "ClaudeNode": ClaudeNode,
    "GoogleVertexNode": GoogleVertexNode,
    "DateNode": DateNode,
    "RandomNode": RandomNode,
    "HistoryNode": HistoryNode,
    "ManualHistoryNode": ManualHistoryNode,
    "HistoryWindow": HistoryWindow,
    "WindowedHistoryNode": WindowedHistoryNode,
    "DynamicWindowedHistoryNode": DynamicWindowedHistoryNode,
    "DummyNode": DummyNode,
    "PromptNode": PromptNode,
    "EmbeddingInNode": EmbeddingInNode,
    "EmbeddingQueryNode": EmbeddingQueryNode,
    "EmbeddingsIngestNode": EmbeddingsIngestNode,
    "AssertNode": AssertNode,
    "LoggingNode": LoggingNode,
    "InterpreterNode": InterpreterNode,
    "EnvNode": EnvNode,
    "ManualEnvNode": ManualEnvNode,
    "WhispersNode": WhispersNode,
    "ElevenLabsNode": ElevenLabsNode,
    "PGQueryNode": PGQueryNode,
    "SQLiteQueryNode": SQLiteQueryNode,
    "PGGenerateNode": PGGenerateNode,
    "JsonNode": JsonNode,
    "JsonerizerNode": JsonerizerNode,
    "SerpApiNode": SerpApiNode,
    "GoogleSearchNode": GoogleSearchNode,
    "FileOutput": FileOutput,
    "JSONFileOutput": JSONFileOutput,
    "HttpNode": HttpNode,
    "JSONRequestNode": JSONRequestNode,
    "ScrapeNode": ScrapeNode,
    "ServerInputNode": ServerInputNode,
    "PineconeInsertNode": PineconeInsertNode,
    "PineconeQueryNode": PineconeQueryNode,
    "DallENode": DallENode,
    "CaptionNode": CaptionNode,
    "OpenImageFile": OpenImageFile,
    "JSONImageFile": JSONImageFile,
    "SaveImageNode": SaveImageNode,
}