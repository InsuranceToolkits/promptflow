"""
This module contains the Flowchart class, which manages the nodes and connectors of a flowchart.
"""
from __future__ import annotations
import logging
import tkinter as tk
import tkinter.scrolledtext
from typing import Any, Optional
from promptflow.src.nodes.node_base import Node
from promptflow.src.nodes.start_node import InitNode, StartNode
from promptflow.src.nodes.func_node import FuncNode
from promptflow.src.nodes.llm_node import LLMNode
from promptflow.src.nodes.date_node import DateNode
from promptflow.src.nodes.random_number import RandomNode
from promptflow.src.nodes.history_node import HistoryNode
from promptflow.src.nodes.dummy_llm_node import DummyNode
from promptflow.src.nodes.prompt_node import PromptNode
from promptflow.src.nodes.memory_node import (
    MemoryNode,
    WindowedMemoryNode,
    DynamicWindowedMemoryNode,
)
from promptflow.src.nodes.embedding_node import (
    EmbeddingInNode,
    EmbeddingQueryNode,
    EmbeddingsIngestNode,
)
from promptflow.src.nodes.test_nodes import AssertNode
from promptflow.src.connectors.connector import Connector
from promptflow.src.connectors.partial_connector import PartialConnector
from promptflow.src.state import State
from promptflow.src.text_data import TextData


class Flowchart:
    """
    Holds the nodes and connectors of a flowchart.
    """

    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.nodes: list[Node] = []
        self.connectors: list[Connector] = []
        self.text_data_registry: dict[str, TextData] = {}
        self.logger = logging.getLogger(__name__)

        self._selected_element: Optional[Node | Connector] = None
        self._partial_connector: Optional[PartialConnector] = None
        self.is_dirty = False
        self.is_running = False
        
        self.add_node(InitNode(self, 10, 10, 100, 100, "Init"))
        self.add_node(StartNode(self, 10, 210, 100, 300, "Start"))

    @classmethod
    def deserialize(cls, canvas: tk.Canvas, data: dict[str, Any]):
        """
        Deserialize a flowchart from a dict onto a canvas
        """
        flowchart = cls(canvas)
        for node_data in data["nodes"]:
            node = eval(node_data["classname"]).deserialize(flowchart, node_data)
            flowchart.add_node(node)
        for connector_data in data["connectors"]:
            node1 = flowchart.find_node(connector_data["node1"])
            node2 = flowchart.find_node(connector_data["node2"])
            connector = Connector(
                canvas, node1, node2, connector_data.get("condition", "")
            )
            flowchart.add_connector(connector)
        flowchart.reset_node_colors()
        canvas.update()
        flowchart.is_dirty = False
        return flowchart

    @property
    def selected_element(self) -> Optional[Node | Connector]:
        """
        Return last touched node
        """
        return self._selected_element

    @selected_element.setter
    def selected_element(self, elem: Optional[Node | Connector]):
        self.logger.info("Selected element changed to %s", elem.label if elem else None)
        # deselect previous node
        if self._selected_element:
            # configure to have solid border
            self.canvas.itemconfig(self._selected_element.item, width=2)
        # select new node
        if elem:
            self.canvas.itemconfig(elem.item, width=4)
        self._selected_element = elem

    @property
    def start_node(self) -> StartNode:
        """
        Find and return the node with the class StartNode
        """
        start_nodes = [node for node in self.nodes if isinstance(node, StartNode)]
        if len(start_nodes) == 0:
            raise ValueError("No start node found")

        if len(start_nodes) == 1:
            return start_nodes[0]

        # sort by number of input connectors
        start_nodes.sort(key=lambda node: len(node.input_connectors))
        return start_nodes[0]
    
    @property
    def init_node(self) -> InitNode:
        """
        Find and returns the single-run InitNode
        """
        return [node for node in self.nodes if isinstance(node, InitNode)][0]

    def find_node(self, node_id: str) -> Node:
        """
        Given a node uuid, find and return the node
        """
        for node in self.nodes:
            if node.id == node_id:
                return node
        raise ValueError(f"No node with id {node_id} found")

    def add_node(self, node: Node):
        """
        Safely insert a node into the flowchart
        """
        while node in self.nodes:
            self.logger.debug("Duplicate node found, adding (copy) to label...")
            node.label += " (copy)"
        self.nodes.append(node)
        self.selected_element = node
        self.is_dirty = True

    def add_connector(self, connector: Connector):
        """
        Safely insert a connector into the flowchart
        """
        self.logger.debug(f"Adding connector {connector}")
        self.connectors.append(connector)
        self.selected_element = connector
        self.is_dirty = True
        
    def initialize(self, state: State, console: tkinter.scrolledtext.ScrolledText) -> State:
        """
        Initialize the flowchart
        """
        init_node = self.init_node
        if init_node.run_once:
            console.insert(tk.END, "\n[System: Already initialized]\n")
            console.see(tk.END)
            return state
        queue = [self.init_node]
        return self.run(state, console, queue)

    def run(self, state: State, console: tkinter.scrolledtext.ScrolledText, queue: list[Node] = None) -> State:
        """
        Given a state, run the flowchart and update the state
        """
        if not queue:
            queue: list[Node] = [self.start_node]
        state = state or State()
        self.is_running = True

        while queue:
            if not self.is_running:
                self.reset_node_colors()
                console.insert(tk.END, "\n[System: Stopped]\n")
                console.see(tk.END)
                return state
            cur_node: Node = queue.pop(0)
            # turn node light yellow while running
            cur_node.canvas.itemconfig(cur_node.item, fill="light yellow")
            cur_node.canvas.update()
            self.logger.info(f"Running node {cur_node.label}")
            try:
                output = cur_node.run_node(state)
            except Exception as node_err:
                self.logger.error(f"Error running node {cur_node.label}: {node_err}")
                if console:
                    console.insert(
                        tk.END, f"[ERROR]{cur_node.label}: {node_err}" + "\n"
                    )
                    console.see(tk.END)
                break
            if console:
                console.insert(tk.END, f"{cur_node.label}: {output}" + "\n")
                console.see(tk.END)
            self.logger.info(f"Node {cur_node.label} output: {output}")
            # turn node light green
            cur_node.canvas.itemconfig(cur_node.item, fill="light green")
            cur_node.canvas.update()

            if output is None:
                self.logger.info(
                    f"Node {cur_node.label} output is None, stopping execution"
                )
                break

            state.result = output

            for connector in cur_node.output_connectors:
                if connector.condition.text.strip():
                    # evaluate condition and only add node2 to queue if condition is true
                    exec(
                        connector.condition.text.strip(),
                        dict(globals()),
                        state.snapshot,
                    )
                    try:
                        cond = state.snapshot["main"](state)  # type: ignore
                    except Exception as node_err:
                        self.logger.error(f"Error evaluating condition: {node_err}")
                        if console:
                            console.insert(
                                tk.END, f"[ERROR]{cur_node.label}: {node_err}" + "\n"
                            )
                            console.see(tk.END)
                        break
                    self.logger.info(
                        f"Condition {connector.condition} evaluated to {cond}"
                    )
                else:
                    cond = True
                if cond:
                    if connector.node2 not in queue:
                        queue.append(connector.node2)
                        break
                    self.logger.info(f"Added node {connector.node2.label} to queue")

        self.reset_node_colors()
        console.insert(tk.END, "\n[System: Done]\n")
        console.see(tk.END)
        return state

    def begin_add_connector(self, node: Node):
        """
        Start adding a connector from the given node.
        """
        if self._partial_connector:
            self._partial_connector.delete(None)
        self._partial_connector = PartialConnector(self, node)
        self.canvas.bind("<Motion>", self._partial_connector.update)
        self.canvas.bind("<Button-1>", self._partial_connector.finish)
        self.canvas.bind("<Escape>", self._partial_connector.delete)

    def serialize(self):
        """
        Write the flowchart to a dictionary
        """
        data: dict[str, Any] = {}
        data["nodes"] = []
        for node in self.nodes:
            data["nodes"].append(node.serialize())
        data["connectors"] = []
        for connector in self.connectors:
            data["connectors"].append(connector.serialize())
        return data

    def remove_node(self, node: Node):
        """
        Remove a node and all connectors connected to it.
        """
        if node in self.nodes:
            self.nodes.remove(node)
        # remove all connectors connected to this node
        for n in self.nodes:
            for connector in n.connectors:
                if connector.node1 == node or connector.node2 == node:
                    connector.delete()
                    if connector in n.input_connectors:
                        n.input_connectors.remove(connector)
                    if connector in n.output_connectors:
                        n.output_connectors.remove(connector)
        for connector in self.connectors:
            if connector.node1 == node or connector.node2 == node:
                connector.delete()
        self.is_dirty = True

    def clear(self):
        """
        Clear the flowchart.
        """
        for node in self.nodes:
            node.delete()
        self.nodes = []
        for connector in self.connectors:
            connector.delete()
        self.connectors = []
        self.canvas.delete("all")
        self.canvas.update()
        self.is_dirty = True

    def reset_node_colors(self):
        """
        Set all node colors to their default color.
        """
        for node in self.nodes:
            self.canvas.itemconfig(node.item, fill=node.node_color)

    def register_text_data(self, text_data: TextData):
        """
        On creation of a TextData object, register it with the flowchart.
        """
        if text_data.label:
            self.logger.debug(f"Registering text data {text_data.label}")
            self.text_data_registry[text_data.label] = text_data

    def cost(self, state: State):
        """
        Return the cost of the flowchart.
        """
        cost = 0
        for node in self.nodes:
            cost += node.cost(state)
        return cost

    def to_mermaid(self):
        """
        Return a mermaid string representation of the flowchart.
        """
        mermaid_str = "graph TD\n"
        for node in self.nodes:
            mermaid_str += f"{node.id}({node.label})\n"
        for connector in self.connectors:
            if connector.condition_label:
                mermaid_str += f"{connector.node1.id} -->|{connector.condition_label}| {connector.node2.id}\n"
            else:
                mermaid_str += f"{connector.node1.id} --> {connector.node2.id}\n"

        return mermaid_str
