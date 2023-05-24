"""
Primary application class. This class is responsible for creating the
window, menu, and canvas. It also handles the saving and loading of
flowcharts.
"""
import json
import logging
import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QSystemTrayIcon, QSplitter, QScrollArea, QMainWindow
from PyQt6.QtGui import QIcon, QPixmap, QAction, QKeySequence, QShortcut
from PyQt6.QtCore import Qt

from PIL import Image, ImageTk
import networkx as nx
import os
from typing import Optional
import zipfile
from PIL import ImageGrab
from promptflow.src.command import (
    CommandManager,
    AddConnectionCommand,
    RemoveConnectionCommand,
    AddNodeCommand,
    RemoveNodeCommand,
)
from promptflow.src.connectors.connector import Connector
from promptflow.src.cursor import FlowchartCursor

from promptflow.src.flowchart import Flowchart
from promptflow.src.nodes.audio_node import ElevenLabsNode, WhispersNode
from promptflow.src.nodes.date_node import DateNode
from promptflow.src.nodes.env_node import EnvNode, ManualEnvNode
from promptflow.src.nodes.http_node import HttpNode, JSONRequestNode, ScrapeNode
from promptflow.src.nodes.image_node import (
    DallENode,
    CaptionNode,
    OpenImageFile,
    JSONImageFile,
    SaveImageNode,
)
from promptflow.src.nodes.memory_node import PineconeInsertNode, PineconeQueryNode
from promptflow.src.nodes.node_base import NodeBase
from promptflow.src.nodes.db_node import (
    PGMLNode,
    PGGenerateNode,
    SQLiteQueryNode,
    PGQueryNode,
)
from promptflow.src.nodes.output_node import FileOutput, JSONFileOutput
from promptflow.src.nodes.regex_node import RegexNode, TagNode
from promptflow.src.nodes.start_node import InitNode, StartNode
from promptflow.src.nodes.prompt_node import PromptNode
from promptflow.src.nodes.func_node import FuncNode
from promptflow.src.nodes.llm_node import ClaudeNode, OpenAINode, GoogleVertexNode
from promptflow.src.nodes.random_number import RandomNode
from promptflow.src.nodes.history_node import (
    HistoryNode,
    ManualHistoryNode,
    HistoryWindow,
    WindowedHistoryNode,
    DynamicWindowedHistoryNode,
)
from promptflow.src.nodes.embedding_node import (
    EmbeddingInNode,
    EmbeddingQueryNode,
    EmbeddingsIngestNode,
)
from promptflow.src.nodes.input_node import FileInput, InputNode, JSONFileInput
from promptflow.src.nodes.server_node import ServerInputNode
from promptflow.src.nodes.structured_data_node import JsonNode, JsonerizerNode
from promptflow.src.nodes.test_nodes import AssertNode, LoggingNode, InterpreterNode
from promptflow.src.nodes.websearch_node import SerpApiNode
from promptflow.src.options import Options
from promptflow.src.nodes.dummy_llm_node import DummyNode
from promptflow.src.state import State
from promptflow.src.themes import monokai
from promptflow.src.dialogues.app_options import AppOptions


class App:
    """
    Primary application class. This class is responsible for creating the
    window, menu, and canvas. It also handles the saving and loading of
    flowcharts.
    """

    def __init__(self, initial_state: State, options: Options):
        self.app = QApplication([])
        self.root = QMainWindow()
        self.root.setWindowTitle("PromptFlow")
        self.loading_popup = self.show_loading_popup("Starting app...")
        self.options = options
        self.initial_state = initial_state
        self.logging_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.logger = logging.getLogger(__name__)
        self.set_dark_mode()

        logging.basicConfig(level=logging.DEBUG, format=self.logging_fmt)
        self.logger.info("Creating app")
        if getattr(sys, "frozen", False):
            ico_dir = sys._MEIPASS
        else:
            ico_dir = os.path.dirname(__file__) + "/../res/"
        # debug file path
        self.logger.info(f"ico_dir: {ico_dir}")
        png_path = os.path.join(ico_dir, "Logo_2.png")
        photo = QIcon(png_path)
        self.root.setWindowIcon(photo)
        # if on windows, use ico
        # if os.name == "nt":
        #     ico_path = os.path.join(ico_dir, "Logo_2.ico")
        #     self.root.wm_iconbitmap(default=ico_path)

        self.tray_icon = QSystemTrayIcon(photo, self.root)
        self.tray_icon.show()

        self.command_manager = CommandManager()  # todo

        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0

        # Build the core components

        self.paned_window = QSplitter(parent=self.root, orientation=Qt.Orientation.Vertical)
        self.canvas = QPixmap(options.width, options.height)
        self.flowchart = Flowchart(self.canvas, root=self.root)
        self.cursor = FlowchartCursor(
            self.canvas, options.width / 2, options.height / 2
        )
        self.current_file = "Untitled"

        # scrolling text meant to simulate a console
        self.output_console_scroll = QScrollArea(self.root)
        self.output_console_scroll.setWidgetResizable(True)
        self.output_console_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.output_console_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.output_console = QLabel(self.root)
        self.output_console.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.output_console.setWordWrap(True)
        self.output_console.setOpenExternalLinks(True)


        # register on close behavior
        # self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        quit = QAction("Quit", self.root)
        quit.triggered.connect(self.on_close)


        # create the menu
        self.menubar = self.root.menuBar()

        self.file_menu = self.menubar.addMenu("&File")
        save_flowchart = QAction("Save Flowchart", self.root)
        save_flowchart.triggered.connect(self.save_as)
        self.file_menu.addAction(save_flowchart)
        load_flowchart = QAction("Load Flowchart", self.root)
        load_flowchart.triggered.connect(self.load_from)
        self.file_menu.addAction(load_flowchart)
        save_console = QAction("Save Console", self.root)
        save_console.triggered.connect(self.export_console)
        self.file_menu.addAction(save_console)

        self.export_menu = self.menubar.addMenu("&Export")
        export_to_mermaid = QAction("To Mermaid", self.root)
        export_to_mermaid.triggered.connect(self.export_to_mermaid)
        self.export_menu.addAction(export_to_mermaid)
        export_to_graphml = QAction("To GraphML", self.root)
        export_to_graphml.triggered.connect(self.export_to_graphml)
        self.export_menu.addAction(export_to_graphml)
        export_to_postscript = QAction("To Postscript", self.root)
        export_to_postscript.triggered.connect(self.export_to_postscript)
        self.export_menu.addAction(export_to_postscript)

        # edit menu for common actions
        self.edit_menu = self.menubar.addMenu("&Edit")
        undo = QAction("Undo", self.root)
        undo.triggered.connect(self.command_manager.undo)
        self.edit_menu.addAction(undo)
        redo = QAction("Redo", self.root)
        redo.triggered.connect(self.command_manager.redo)
        self.edit_menu.addAction(redo)
        clear = QAction("Clear", self.root)
        clear.triggered.connect(self.clear_flowchart)
        self.edit_menu.addAction(clear)
        options_ = QAction("Options", self.root)
        options_.triggered.connect(self.edit_options)
        self.edit_menu.addAction(options_)


        # create an add menu for each type of node
        self.add_menu = self.menubar.addMenu("&Add")
        self.add_menu.addAction("Start - First node in main loop", self.create_add_node_function(StartNode, "Start"))
        self.add_menu.addAction("Initialize - Run this subchart once", self.create_add_node_function(InitNode, "Initialize"))
        self.envvars_menu = self.add_menu.addMenu("Environment Variables")
        self.envvars_menu.addAction(".env - Load environment variables from .env file", self.create_add_node_function(EnvNode, ".env"))
        self.envvars_menu.addAction("Manual - Manually set environment variables", self.create_add_node_function(ManualEnvNode, "Manual"))
        self.input_menu = self.add_menu.addMenu("Input")
        self.input_menu.addAction("Input - Pause for user input", self.create_add_node_function(InputNode, "Input"))
        self.input_menu.addAction("Server - Listen for input on a port", self.create_add_node_function(ServerInputNode, "Server"))
        self.input_menu.addAction("File - Read file from disk", self.create_add_node_function(FileInput, "File"))
        self.input_menu.addAction("JSON Parsed File - Read file from disk parsed from JSON", self.create_add_node_function(JSONFileInput, "JSON Input File"))
        self.output_menu = self.add_menu.addMenu("Output")
        self.output_menu.addAction("File - Write to file on disk", self.create_add_node_function(FileOutput, "File"))
        self.output_menu.addAction("JSON Parsed File - Write to file on disk parsed from JSON", self.create_add_node_function(JSONFileOutput, "JSON Output File"))
        self.add_menu.addAction("Prompt - Format custom text", self.create_add_node_function(PromptNode, "Prompt"))
        self.add_menu.addAction("Function - Custom Python Function", self.create_add_node_function(FuncNode, "Function"))
        self.llm_menu = self.add_menu.addMenu("LLM")
        self.llm_menu.addAction("OpenAI - Pass text to OpenAI model of choice", self.create_add_node_function(OpenAINode, "OpenAI"))
        self.llm_menu.addAction("Claude - Pass text to Anthropic Claude", self.create_add_node_function(ClaudeNode, "Claude"))
        self.llm_menu.addAction("Google - Pass text to Google LLM", self.create_add_node_function(GoogleVertexNode, "Google"))
        self.history_menu = self.add_menu.addMenu("History")
        self.history_menu.addAction("History - Save result to chat history", self.create_add_node_function(HistoryNode, "History"))
        self.history_menu.addAction("Manual History - Manually set chat history", self.create_add_node_function(ManualHistoryNode, "Manual History"))
        self.history_menu.addAction("Windowed History - Save to history with a window", self.create_add_node_function(WindowedHistoryNode, "Windowed History"))
        self.history_menu.addAction("Dynamic Windowed History - Save to history based on last occurrence of text", self.create_add_node_function(DynamicWindowedHistoryNode, "Dynamic Windowed history"))
        self.memory_menu = self.add_menu.addMenu("Memory")
        self.memory_menu.addAction("Pinecone Insert - Insert data into Pinecone", self.create_add_node_function(PineconeInsertNode, "Pinecone Insert"))
        self.memory_menu.addAction("Pinecone Query - Query data from Pinecone", self.create_add_node_function(PineconeQueryNode, "Pinecone Query"))
        self.requests_menu = self.add_menu.addMenu("Requests")
        self.requests_menu.addAction("HTTP - Send HTTP request", self.create_add_node_function(HttpNode, "HTTP"))
        self.requests_menu.addAction("JSON Request - Send HTTP request to a url parsed from JSON", self.create_add_node_function(JSONRequestNode, "JSON-Parsed Request"))
        self.requests_menu.addAction("Scrape - Scrape text from a url", self.create_add_node_function(ScrapeNode, "Scrape"))
        self.regex_menu = self.add_menu.addMenu("Regex")
        self.regex_menu.addAction("Regex - Match text with regex", self.create_add_node_function(RegexNode, "Regex"))
        self.regex_menu.addAction("Tag - Extract text between tags", self.create_add_node_function(TagNode, "Tag"))
        self.structured_data_menu = self.add_menu.addMenu("Structured Data")
        self.structured_data_menu.addAction("JSON - Parse and validate JSON", self.create_add_node_function(JsonNode, "JSON"))
        self.structured_data_menu.addAction("JSONerizer - Parse JSON from text", self.create_add_node_function(JsonerizerNode, "JSONerizer"))
        self.search_nodes_menu = self.add_menu.addMenu("Search Nodes")
        self.search_nodes_menu.addAction("SerpAPI - Search Google with SerpAPI", self.create_add_node_function(SerpApiNode, "SerpAPI"))
        self.embedding_menu = self.add_menu.addMenu("Embedding")
        self.embedding_menu.addAction("Embedding In - Embed result and save to hnswlib", self.create_add_node_function(EmbeddingInNode, "Embedding In"))
        self.embedding_menu.addAction("Embedding Query - Query HNSW index", self.create_add_node_function(EmbeddingQueryNode, "Embedding Query"))
        self.embedding_menu.addAction("Embedding Ingest - Read embeddings from file. Use with init node.", self.create_add_node_function(EmbeddingsIngestNode, "Embedding Ingest"))
        self.db_menu = self.add_menu.addMenu("Database")
        self.db_menu.addAction("Query - Query a SQLite database", self.create_add_node_function(SQLiteQueryNode, "SQLite Query"))
        self.db_menu.addAction("PG Query - Query a PostgreSQL database", self.create_add_node_function(PGQueryNode, "PG Query"))
        self.db_menu.addAction("Generate - Generate next text from PGML model", self.create_add_node_function(PGGenerateNode, "Generate"))
        self.add_menu.addAction("Date - Insert current datetime", self.create_add_node_function(DateNode, "Date"))
        self.add_menu.addAction("Random - Insert a random number", self.create_add_node_function(RandomNode, "Random"))
        self.test_menu = self.add_menu.addMenu("Test")
        self.test_menu.addAction("Logging - Print string to log", self.create_add_node_function(LoggingNode, "Logging"))
        self.test_menu.addAction("Interpreter - Open a Python interpreter", self.create_add_node_function(InterpreterNode, "Interpreter"))
        self.test_menu.addAction("Dummy LLM - For testing", self.create_add_node_function(DummyNode, "Dummy LLM"))
        self.test_menu.addAction("Assert - Assert certain condition is true", self.create_add_node_function(AssertNode, "Assert"))
        self.audio_menu = self.add_menu.addMenu("Audio")
        self.audio_menu.addAction("Whisper Audio Input - Record audio", self.create_add_node_function(WhispersNode, "Whisper Audio Input"))
        self.audio_menu.addAction("ElevenLabs Audio Output - Text-to-speech", self.create_add_node_function(ElevenLabsNode, "ElevenLabs Audio Output"))
        self.image_menu = self.add_menu.addMenu("Image")
        self.image_menu.addAction("Dall-E - Generate image from text", self.create_add_node_function(DallENode, "Dall-E"))
        self.image_menu.addAction("Open File - Open image from file", self.create_add_node_function(OpenImageFile, "Open File"))
        self.image_menu.addAction("JSON File - Open image from file parsed from JSON", self.create_add_node_function(JSONImageFile, "JSON File"))
        self.image_menu.addAction("Save Image - Save image to file", self.create_add_node_function(SaveImageNode, "Save Image"))
        self.image_menu.addAction("Caption - Caption an image", self.create_add_node_function(CaptionNode, "Caption"))

        # create the "Arrange" menu
        self.arrange_menu = self.menubar.addMenu("&Arrange")
        self.arrange_menu.addAction("Tree Layout", self.arrange_tree)
        self.arrange_menu.addAction("Bipartite Layout", lambda: self.arrange_networkx(nx.layout.bipartite_layout))
        self.arrange_menu.addAction("Circular Layout", lambda: self.arrange_networkx(nx.layout.circular_layout))
        self.arrange_menu.addAction("Kamada Kawai Layout", lambda: self.arrange_networkx(nx.layout.kamada_kawai_layout))
        self.arrange_menu.addAction("Planar Layout", lambda: self.arrange_networkx(nx.layout.planar_layout))
        self.arrange_menu.addAction("Random Layout", lambda: self.arrange_networkx(nx.layout.random_layout))
        self.arrange_menu.addAction("Shell Layout", lambda: self.arrange_networkx(nx.layout.shell_layout))
        self.arrange_menu.addAction("Spring Layout", lambda: self.arrange_networkx(nx.layout.spring_layout))
        self.arrange_menu.addAction("Spectral Layout", lambda: self.arrange_networkx(nx.layout.spectral_layout))
        self.arrange_menu.addAction("Spiral Layout", lambda: self.arrange_networkx(nx.layout.spiral_layout))

        # create a help menu
        self.help_menu = self.menubar.addMenu("&Help")
        self.help_menu.addAction("About PromptFlow...", self.show_about)

        # create the toolbar
        self.toolbar = self.root.addToolBar("Toolbar")
        self.run_button = QAction("Run", self.root)
        self.run_button.triggered.connect(self.run_flowchart)
        self.toolbar.addAction(self.run_button)
        self.stop_button = QAction("Stop", self.root)
        self.stop_button.triggered.connect(self.stop_flowchart)
        self.toolbar.addAction(self.stop_button)
        self.serialize_button = QAction("Serialize", self.root)
        self.serialize_button.triggered.connect(self.serialize_flowchart)
        self.toolbar.addAction(self.serialize_button)
        self.screenshot_button = QAction("Screenshot", self.root)
        self.screenshot_button.triggered.connect(self.save_image)
        self.toolbar.addAction(self.screenshot_button)
        self.cost_button = QAction("Cost", self.root)
        self.cost_button.triggered.connect(self.cost_flowchart)
        self.toolbar.addAction(self.cost_button)

        self.toolbar_buttons = [
            self.run_button,
            self.stop_button,
            self.serialize_button,
            self.screenshot_button,
            self.cost_button,
        ]

        # key bindings
        self._create_key_bindings()

        # add the menu
        self.root.update()

        self.logger.debug("App created")
        self.loading_popup.destroy()

    def _create_key_bindings(self):
        """Create the key bindings for the app"""
        self.logger.debug("Creating key bindings")
        ctrl_s = QShortcut(QKeySequence("Ctrl+S"), self.root)
        ctrl_s.activated.connect(self.save_as)
        ctrl_o = QShortcut(QKeySequence("Ctrl+O"), self.root)
        ctrl_o.activated.connect(self.load_from)
        f5 = QShortcut(QKeySequence("F5"), self.root)
        f5.activated.connect(self.run_flowchart)
        ctrl_r = QShortcut(QKeySequence("Ctrl+R"), self.root)
        ctrl_r.activated.connect(self.run_flowchart)
        delete = QShortcut(QKeySequence("Delete"), self.root)
        delete.activated.connect(self.delete_selected_element)
        mouse_wheel = QShortcut(QKeySequence("Ctrl+Wheel"), self.root)
        mouse_wheel.activated.connect(self.handle_zoom)
        mouse_wheel_up = QShortcut(QKeySequence("Wheel"), self.root)
        mouse_wheel_up.activated.connect(self.handle_zoom)
        mouse_wheel_down = QShortcut(QKeySequence("Shift+Wheel"), self.root)
        mouse_wheel_down.activated.connect(self.handle_zoom)
        mouse_wheel_up_mac = QShortcut(QKeySequence("4"), self.root)
        mouse_wheel_up_mac.activated.connect(self.handle_zoom)
        mouse_wheel_down_mac = QShortcut(QKeySequence("5"), self.root)
        mouse_wheel_down_mac.activated.connect(self.handle_zoom)
        middle_mouse_button = QShortcut(QKeySequence("ButtonPress-2"), self.root)
        middle_mouse_button.activated.connect(self.start_pan)
        middle_mouse_button_drag = QShortcut(QKeySequence("B2-Motion"), self.root)
        middle_mouse_button_drag.activated.connect(self.pan)
        left_mouse_button = QShortcut(QKeySequence("Button-1"), self.root)
        left_mouse_button.activated.connect(self.log_click)
 
    def log_click(self, *args, **kwargs):
        """Print the coordinates of the mouse click"""
        self.logger.debug(f"Mouse click: {args}, {kwargs}")

    @property
    def current_file(self) -> str:
        """The current file being edited."""
        return self._current_file

    @current_file.setter
    def current_file(self, value: str):  
        self.root.setWindowTitle(f"PromptFlow - {value}")
        self._current_file = value

    def run_flowchart(self) -> None:
        """Execute the flowchart."""
        self.logger.info("Running flowchart")
        init_state = self.initial_state.copy()
        init_state = self.flowchart.initialize(init_state, self.output_console)
        final_state = self.flowchart.run(init_state, self.output_console)
        self.logger.info("Finished running flowchart")
        self.initial_state.reset()

    def stop_flowchart(self):
        """Stop the flowchart."""
        self.logger.info("Stopping flowchart")
        self.flowchart.is_running = False
        self.flowchart.is_dirty = True
        self.initial_state.reset()

    def serialize_flowchart(self) -> None:
        """Serialize the flowchart to JSON."""
        self.logger.info("Serializing flowchart")
        chart_json = json.dumps(self.flowchart.serialize(), indent=4)
        self.logger.info(chart_json)
        # self.output_console.insert(tk.INSERT, chart_json)
        # self.output_console.see(tk.END)
        self.output_console.setText(chart_json)

    def clear_flowchart(self):
        """Clear the flowchart."""
        # ask the user if they want to save
        if self.flowchart.nodes and not self.flowchart.is_running:
            save = tk.messagebox.askyesnocancel(
                "Save?",
                "Would you like to save before clearing?",
                parent=self.root,
            )
            if save is None:
                return
            elif save:
                self.save_as()
        self.logger.info("Clearing flowchart")
        self.flowchart.clear()
        self.initial_state.reset()
        self.output_console.delete("1.0", tk.END)

    def edit_options(self):
        """
        Show the options popup
        """
        options_popup = AppOptions(self.canvas, self.options)
        self.canvas.wait_window(options_popup)

    def cost_flowchart(self):
        """Get the approx cost to run the flowchart"""
        self.logger.info("Getting cost of flowchart")
        state = self.initial_state.copy()
        cost = self.flowchart.cost(state)
        self.output_console.insert(tk.INSERT, f"Estimated Cost: {cost}\n")
        self.output_console.see(tk.END)

    def run(self):
        """Run the app."""
        self.logger.info("Running app")
        self.root.show()
        self.app.exec()

    def save_image(self):
        """
        Render the canvas as a png file and save it to image.png
        """
        self.logger.info("Saving image to image.png")
        x = self.canvas.winfo_rootx() + self.canvas.winfo_x()
        y = self.canvas.winfo_rooty() + self.canvas.winfo_y()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()
        ImageGrab.grab().crop((x, y, x1, y1)).save("image.png")

    def save_as(self):
        """
        Serialize the flowchart and save it to a json file
        """
        filename = tkinter.filedialog.asksaveasfilename(defaultextension=".promptflow")
        if filename:
            self.loading_popup = self.show_loading_popup("Saving flowchart...")
            with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(
                    "flowchart.json", json.dumps(self.flowchart.serialize(), indent=4)
                )
                # if there's an embedding ingest node, save the embedding
                for node in self.flowchart.nodes:
                    if isinstance(node, EmbeddingsIngestNode):
                        # write the embedding to the archive
                        archive.write(node.filename, arcname=node.filename)
                        archive.write(node.label_file, arcname=node.label_file)
                self.logger.info("Saved flowchart to %s", filename)
                self.current_file = filename
                self.loading_popup.destroy()
        else:
            self.logger.info("No file selected to save to")
        self.flowchart.is_dirty = False

    def load_from(self):
        """
        Read a json file and deserialize as a flowchart
        """
        filename = tkinter.filedialog.askopenfilename()
        if filename:
            self.loading_popup = self.show_loading_popup("Loading flowchart...")
            self.clear_flowchart()
            with zipfile.ZipFile(filename, "r") as archive:
                with archive.open("flowchart.json") as loadfile:
                    data = json.load(loadfile)
                    # load the embedding if there is one
                    for node in data["nodes"]:
                        if node["classname"] == "EmbeddingsIngestNode":
                            # load the embedding
                            embed_file = archive.extract(
                                node["filename"], path=os.getcwd()
                            )
                            node["filename"] = embed_file
                            # load the labels
                            label_file = archive.extract(
                                node["label_file"], path=os.getcwd()
                            )
                            node["label_file"] = label_file
                    self.clear_flowchart()
                    self.flowchart = Flowchart.deserialize(
                        self.canvas, data, (self.pan_x, self.pan_y), self.zoom_level
                    )
                    self.current_file = filename
                    self.loading_popup.destroy()
        else:
            self.logger.info("No file selected to load from")

    def create_add_node_function(self, node_class, name="New Node"):
        """
        Create a function that adds a node to the flowchart
        """

        def add_node():
            node = node_class(
                self.flowchart, self.cursor.center_x, self.cursor.center_y, name
            )
            self.flowchart.add_node(node)
            # scale node
            for item in node.items:
                self.canvas.scale(
                    item,
                    self.cursor.center_x,
                    self.cursor.center_y,
                    self.zoom_level,
                    self.zoom_level,
                )
            for button in node.buttons:
                button.configure(width=button.cget("width") * self.zoom_level)
                button.configure(height=button.cget("height") * self.zoom_level)

        return add_node

    def on_close(self):
        """
        Called when the user tries to close the app
        Checks if the flowchart is dirty and gives the user the option to save
        """
        self.logger.info("Closing app")
        if self.flowchart.nodes and self.flowchart.is_dirty:
            # give user option to save file before closing
            dialog = tkinter.messagebox.askyesnocancel(
                "Quit", "Do you want to save your work?"
            )
            if dialog is True:
                self.save_as()
            elif dialog is None:
                return  # don't close
        self.root.destroy()

    def show_about(self):
        """
        Show the about dialog
        """
        self.logger.info("Showing about")
        tkinter.messagebox.showinfo("About", "PromptFlow")

    def delete_selected_element(self):
        """
        When the user presses delete, delete the selected node if there is one
        """
        if self.flowchart.selected_element:
            self.logger.info(
                f"Deleting selected element {self.flowchart.selected_element.label}"
            )
            self.flowchart.selected_element.delete()
            if isinstance(self.flowchart.selected_element, NodeBase):
                self.flowchart.graph.remove_node(self.flowchart.selected_element)
            elif isinstance(self.flowchart.selected_element, Connector):
                self.flowchart.graph.remove_edge(
                    self.flowchart.selected_element.node1,
                    self.flowchart.selected_element.node2,
                )

    def handle_zoom(self, event):
        """
        Zoom in or out when the user scrolls
        """
        zoom_scale = 1.0

        # Check the platform
        if (
            event.num == 4 or event.delta > 0
        ):  # Linux (wheel up) or Windows (positive delta)
            zoom_scale = 1.1
        elif (
            event.num == 5 or event.delta < 0
        ):  # Linux (wheel down) or Windows (negative delta)
            zoom_scale = 0.9
        else:  # MacOS
            delta = event.delta
            if delta > 0:
                zoom_scale = 1.1
            elif delta < 0:
                zoom_scale = 0.9

        self.canvas.scale("all", event.x, event.y, zoom_scale, zoom_scale)
        for node in self.flowchart.nodes:
            for button in node.buttons:
                button.configure(width=button.cget("width") * zoom_scale)
                button.configure(height=button.cget("height") * zoom_scale)
                # button.cget("font").configure(size=int(button.cget("font").cget("size") * zoom_scale))
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.zoom_level *= zoom_scale

    def start_pan(self, event):
        """Begining drag to scroll canvas"""
        self.canvas.scan_mark(event.x, event.y)

    def pan(self, event):
        """Dragging to scroll canvas"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.pan_x = self.canvas.canvasx(event.x)
        self.pan_y = self.canvas.canvasy(event.y)
        self.cursor.move_to(self.pan_x, self.pan_y)

    def show_loading_popup(self, message: str):
        """Show the loading popup"""
        # Create a new Toplevel widget for the loading popup
        popup = QMainWindow(self.root)
        popup.setWindowTitle("Please wait...")
        popup.setGeometry(300, 300, 300, 100)

        # Create a label with the loading message
        label = QLabel(popup)
        label.setText(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return popup

    def export_to_mermaid(self):
        """
        Print the flowchart in the mermaid flowchart language
        """
        self.logger.info("Exporting flowchart")
        self.output_console.insert(tk.END, self.flowchart.to_mermaid())

    def export_to_graphml(self):
        """
        Print the flowchart in the graphml format
        """
        self.logger.info("Exporting flowchart")
        self.output_console.insert(tk.END, self.flowchart.to_graph_ml())

    def export_to_postscript(self):
        """
        Print the flowchart in the postscript format
        """
        self.logger.info("Exporting flowchart")
        # open file dialog
        file_dialog = tkinter.filedialog.asksaveasfile(mode="w", defaultextension=".ps")
        if file_dialog:
            self.output_console.insert(
                tk.END, self.flowchart.to_postscript(file_dialog.name)
            )

    def export_console(self):
        """
        Write the contents console to a file
        """
        self.logger.info("Exporting console")
        # create file dialog
        filedialog = tkinter.filedialog.asksaveasfile(mode="w", defaultextension=".txt")
        if filedialog:
            filedialog.write(self.output_console.get("1.0", tk.END))
            filedialog.close()

    def arrange_tree(self):
        if self.flowchart.init_node:
            self.flowchart.arrange_tree(self.flowchart.init_node)
            for node in self.flowchart.nodes:
                node.visited = False
        self.flowchart.arrange_tree(self.flowchart.start_node, NodeBase.size_px + 60)
        for node in self.flowchart.nodes:
            node.visited = False

    def arrange_networkx(self, algorithm):
        self.flowchart.arrange_networkx(algorithm)

    def set_dark_mode(self):
        """
        Set the theme to dark mode
        """
        self.logger.info("Setting theme to dark mode")