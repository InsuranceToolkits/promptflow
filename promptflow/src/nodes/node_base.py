"""
Base class for all nodes
"""
from typing import TYPE_CHECKING, Any, Optional
from abc import ABC, abstractmethod
import logging
import uuid
from PyQt6.QtWidgets import QTextEdit, QMainWindow, QPushButton
from PyQt6.QtGui import QPixmap, QAction, QPainter
from PyQt6.QtCore import Qt
from promptflow.src.state import State
from promptflow.src.serializable import Serializable
from promptflow.src.themes import monokai

if TYPE_CHECKING:
    from promptflow.src.flowchart import Flowchart
    from promptflow.src.connectors.connector import Connector


class NodeBase(Serializable, ABC):
    """
    Represents a node in the flowchart, which could be a prompt, an llm, traditional code, etc.
    """

    node_color = monokai.WHITE
    prev_color = node_color
    size_px: int = 50  # arbitrary default size

    def __init__(
        self,
        flowchart: "Flowchart",
        center_x: float,
        center_y: float,
        label: str,
        root: QMainWindow,
        **kwargs,
    ):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Creating node %s", label)
        self.flowchart = flowchart
        self.id: str = kwargs.get("id") or str(uuid.uuid1())
        self.canvas: QPixmap = flowchart.canvas
        self.root = root 

        self.item = self.draw_shape(center_x, center_y)
        self.bind_canvas_events()
        # right click menu
        # right_click_menu = QAction(text="Right Click Menu", parent=self.canvas)
        # right_click_menu.triggered.connect(self.show_menu)
        
        self._label = label
        self.input_connectors: list[Connector] = []
        self.output_connectors: list[Connector] = []
        self.visited = False  # Add a visited attribute to keep track of visited nodes

        # create the label
        self.center_x = center_x
        self.center_y = center_y
        painter = QPainter(self.canvas)
        self.label_item = painter.drawText(
            int(center_x),
            int(center_y),
            label,
        )
        # self.canvas.tag_bind(self.label_item, "<Double-Button-1>", self.edit_label)
        # bind double click to edit label
        double_click = QAction(text="Double Click", parent=root)
        double_click.triggered.connect(self.edit_label)
        root.addAction(double_click)


        # self.add_connector_button = QPushButton(
        #     self.canvas,
        #     text="+",
        #     command=self.begin_add_connector,
        #     width=38,
        #     corner_radius=4,
        #     border_width=2,
        #     border_color="black",
        # )
        self.add_connector_button = QPushButton(
            parent=self.root,
            text="+",
        )
        # add to pixmap

        # self.delete_button = customtkinter.CTkButton(
        #     self.canvas,
        #     text="x",
        #     command=lambda: self.delete(show_confirmation=True),
        #     width=38,
        #     corner_radius=4,
        #     border_width=2,
        #     border_color="black",
        # )
        # self.delete_item = self.canvas.create_window(
        #     center_x - 23, center_y + 68, window=self.delete_button
        # )
        self.delete_button = QPushButton(
            parent=self.root,
            text="x",
        )

        self.items = [
            self.label_item,
            self.delete_button,
            self.add_connector_button,
            self.item,
        ]

        self.bind_drag()
        self.bind_mouseover()
        # self.canvas.tag_bind(self.item, "<Double-Button-1>", self.edit_options)
        edit_action = QAction(text="Edit", parent=root)
        edit_action.triggered.connect(self.edit_options)

        self.buttons = [self.delete_button, self.add_connector_button]

        self.label_entry: Optional[customtkinter.CTkEntry] = None

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, NodeBase):
            return self.id == __o.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)

    def bind_canvas_events(self):
        """
        Bind events to the canvas.
        """
        self.canvas.mousePressEvent = self.start_drag
        self.canvas.mouseReleaseEvent = self.stop_drag
        self.canvas.mouseMoveEvent = self.on_drag


    @property
    def connectors(self) -> list["Connector"]:
        """All connectors attached to this node"""
        return self.input_connectors + self.output_connectors

    @classmethod
    def deserialize(cls, flowchart: "Flowchart", data: dict):
        return cls(
            flowchart,
            **data,
        )

    @property
    def label(self) -> str:
        """Name of the node. Used for snapshotting."""
        return self._label

    @label.setter
    def label(self, label: str):
        self._label = label
        self.canvas.itemconfig(self.label_item, text=label, width=self.size_px * 2)

    def get_center(
        self, offset_x: float = 0, offset_y: float = 0
    ) -> tuple[float, float]:
        """
        Node is defined by its top left and bottom right coordinates.
        This function returns the center of the node based on those coordinates.
        """
        center_x = (
            self.canvas.coords(self.item)[0] + self.canvas.coords(self.item)[2]
        ) / 2 + offset_x
        center_y = (
            self.canvas.coords(self.item)[1] + self.canvas.coords(self.item)[3]
        ) / 2 + offset_y
        return center_x, center_y

    def bind_mouseover(self):
        """
        Binds the mouseover events to all the node's items
        """
        # self.canvas.tag_bind(self.item, "<Enter>", self.on_mouseover)
        # self.canvas.tag_bind(self.item, "<Leave>", self.on_mouseleave)
        # for item in self.items:
        #     self.canvas.tag_bind(item, "<Enter>", self.on_mouseover)
        #     self.canvas.tag_bind(item, "<Leave>", self.on_mouseleave)
        self.actions = {}
        for item in self.items:
            self.actions[item] = QAction(text="Mouseover", parent=self.root)
            self.actions[item].triggered.connect(self.on_mouseover)

    def on_mouseover(self, _):
        """
        Darken the color of the node when the mouse is over it.
        """
        self.prev_color = self.canvas.itemcget(self.item, "fill")
        shade = 0.2
        cur_tuple = self.canvas.itemcget(self.item, "fill")
        cur_tuple = tuple(int(cur_tuple[i : i + 2], 16) for i in (1, 3, 5))
        color = "#" + "".join(
            [hex(int(cur_tuple[i] * (1 - shade)))[2:] for i in range(3)]
        )
        self.canvas.itemconfig(self.item, fill=color)
        # make cursor a hand
        self.canvas.configure(cursor="hand2")

    def on_mouseleave(self, _):
        """
        Restore the color of the node when the mouse leaves it.
        """
        self.canvas.itemconfig(self.item, fill=self.prev_color)
        self.canvas.configure(cursor="arrow")

    def edit_label(self, _):
        """
        Start editing the label of the node.
        """
        self.canvas.delete(self.label_item)
        self.items.remove(self.label_item)
        center_x, center_y = self.get_center()
        self.label_entry = customtkinter.CTkEntry(self.canvas)
        self.label_entry.insert(0, self.label)
        self.label_entry.bind("<Return>", self.finish_edit_label)
        self.label_entry.bind("<FocusOut>", self.finish_edit_label)
        self.canvas.create_window(center_x, center_y, window=self.label_entry)

    def finish_edit_label(self, _):
        """
        Called when the user is done editing the label.
        Creates a new label item and destroys the entry.
        """
        if self.label_entry is None:
            return
        self.label = self.label_entry.get()
        self.label_entry.destroy()
        self.label_entry = None
        center_x, center_y = self.get_center()
        self.label_item = self.canvas.create_text(
            center_x,
            center_y,
            text=self.label,
            fill="black",
            width=self.size_px * 2,
            justify="center",
        )
        self.canvas.itemconfig(self.label_item, width=self.size_px * 2)
        self.items.append(self.label_item)
        self.canvas.tag_bind(self.label_item, "<Double-Button-1>", self.edit_label)
        self.bind_drag()
        self.bind_mouseover()

    def begin_add_connector(self):
        """
        Start adding a connector to this node.
        Creates a temporary connector that follows the mouse.
        """
        self.flowchart.begin_add_connector(self)

    def start_drag(self, event):
        """
        Update the flowchart's selected node and start dragging the node by
        updating the node's x and y coordinates.
        """
        self.flowchart.selected_element = self
        self.center_x = event.x
        self.center_y = event.y

    def on_drag(self, event):
        """
        Continuously update the node's position while dragging.
        Update all connectors to follow the node.
        """
        delta_x = event.x - self.center_x
        delta_y = event.y - self.center_y
        for item in self.items:
            self.canvas.move(item, delta_x, delta_y)
        if self.label_entry is not None:
            # destroy the label entry if it exists
            self.finish_edit_label(event)
            self.label_entry = None
        self.center_x = event.x
        self.center_y = event.y
        for connector in self.connectors:
            connector.update()

    def stop_drag(self, _):
        """
        Required to be able to drag the node.
        """

    @abstractmethod
    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        """
        Code that will be run when the node is executed.
        """

    def before(self, state: State, console: QTextEdit) -> Any:
        """
        Blocking method called before main node execution.
        """

    def run_node(
        self, before_result: Any, state: State, console: QTextEdit
    ) -> str:
        """
        Run the node and all nodes connected to it
        Handles setting the snapshot and returning the output.
        """
        state.snapshot[self.label] = state.snapshot.get(self.label, "")
        output: str = self.run_subclass(before_result, state, console)
        state.snapshot[self.label] = output
        state.result = output
        return output

    def serialize(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "center_x": self.center_x,
            "center_y": self.center_y,
            "classname": self.__class__.__name__,
        }

    def delete(self, show_confirmation: bool = False):
        """
        Delete the node and all connectors attached to it.
        """
        if show_confirmation:
            if not tk.messagebox.askyesno(
                "Delete Node", f"Are you sure you want to delete {self.label}?"
            ):
                return
        self.logger.info(f"Deleting node {self.label}")
        self.flowchart.remove_node(self)
        for item in self.items:
            self.logger.debug(f"Deleting item {item}")
            self.canvas.delete(item)

        if self.label_entry is not None:
            self.label_entry.destroy()

        for button in self.buttons:
            button.destroy()

    def copy(self) -> "NodeBase":
        """
        Create a copy of the node, without copying the connectors.
        """
        self.logger.info(f"Copying node {self.label}")
        data = self.serialize()
        data["id"] = uuid.uuid4()
        data["label"] = f"{data['label']} copy"
        new_node = self.deserialize(self.flowchart, data)
        return new_node

    def show_menu(self, event):
        """
        Right-click convenience menu.
        """
        menu = tk.Menu(self.canvas, tearoff=0)
        menu.add_command(label="Delete", command=self.delete)
        menu.add_command(label="Copy", command=self.copy)
        menu.post(event.x_root, event.y_root)

    def get_children(self) -> list["NodeBase"]:
        """
        Return all child nodes of this node.
        """
        return [connector.node2 for connector in self.output_connectors]

    def draw_shape(self, center_x: float, center_y: float):
        """
        Takes the coordinates of the top left and bottom right corners of the node
        Draws the shape of the node
        Rectangles by default
        """
        return self.canvas.create_rectangle(
            center_x - self.size_px,
            center_y - self.size_px,
            center_x + self.size_px,
            center_y + self.size_px,
            fill=self.node_color,
            outline="black",
            tags="node",
        )

    def bind_drag(self):
        """
        Binds the drag events to all the node's items
        Allows behavior like dragging the node by its label
        """
        self.actions = {}
        for item in self.items:
            self.actions[item] = QAction(text="Drag", parent=self.root)
            self.actions[item].triggered.connect(self.start_drag)

    def edit_options(self, event):
        """
        Callback for the edit options button.
        Doesn't do anything by default.
        """

    def cost(self, state: State) -> float:
        """
        The cost of running this node in dollars.
        Adds the label to the snapshot as well for
        prompt formatting.
        """
        state.snapshot[self.label] = ""
        return 0.0

    def move_to(self, x: float, y: float):
        """
        Move the node to the given coordinates.
        """
        delta_x = x - self.center_x
        delta_y = y - self.center_y
        for item in self.items:
            self.canvas.move(item, delta_x, delta_y)
        self.center_x = x
        self.center_y = y
