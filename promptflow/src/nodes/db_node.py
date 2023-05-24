from abc import ABC
import logging
from PyQt6.QtWidgets import QTextEdit
from typing import Any, Callable, Optional, TYPE_CHECKING
from promptflow.src.db_interface.main import (
    PGInterface,
    PgMLInterface,
    SQLBase,
    SQLiteInterface,
)
from promptflow.src.dialogues.node_options import NodeOptions
from promptflow.src.nodes.node_base import NodeBase
from promptflow.src.themes import monokai

if TYPE_CHECKING:
    from promptflow.src.flowchart import Flowchart


class DBConnectionSingleton:
    _instance: Optional["DBConnectionSingleton"] = None
    interface_factory: Callable[[str, str, str, str, str], SQLBase]
    interface: SQLBase
    dbname: str
    user: str
    password: str
    host: str
    port: str

    def __new__(cls, interface) -> "DBConnectionSingleton":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.dbname = "postgres"
            cls._instance.user = "postgres"
            cls._instance.password = "pass"
            cls._instance.host = "localhost"
            cls._instance.port = "5432"
            cls._instance.interface_factory = interface
            cls._instance.interface = interface(
                cls._instance.dbname,
                cls._instance.user,
                cls._instance.password,
                cls._instance.host,
                cls._instance.port,
            )
        return cls._instance

    def update(
        self,
        dbname: str,
        user: str = "",
        password: str = "",
        host: str = "",
        port: str = "",
    ):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.interface = self.interface_factory(
            self.dbname, self.user, self.password, self.host, self.port
        )
        logging.info("connecting to db %s", self.dbname)
        self.interface.connect()
        logging.info("connected to db %s", self.dbname)


class DBNode(NodeBase, ABC):
    node_color = monokai.GREEN

    def __init__(
        self,
        flowchart: "Flowchart",
        center_x: float,
        center_y: float,
        label: str,
        interface,
        **kwargs,
    ):
        self.interface = DBConnectionSingleton(interface=interface)
        self.dbname = self.interface.dbname
        self.user = self.interface.user
        self.password = self.interface.password
        self.host = self.interface.host
        self.port = self.interface.port

        super().__init__(flowchart, center_x, center_y, label, **kwargs)

        self.options_popup: Optional[NodeOptions] = None

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "dbname": self.dbname,
                "user": self.user,
                "password": self.password,
                "host": self.host,
                "port": self.port,
            },
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        if self.options_popup.cancelled:
            return
        self.dbname = result["dbname"]
        self.user = result["user"]
        self.password = result["password"]
        self.host = result["host"]
        self.port = result["port"]  # maybe make an int?
        self.interface.update(
            self.dbname, self.user, self.password, self.host, self.port
        )

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        self.interface.interface.connect()
        return state.result


class SQLiteNode(DBNode):
    node_color = monokai.GREEN

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.interface = DBConnectionSingleton(SQLiteInterface)

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "dbpath": self.dbname,
            },
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        if self.options_popup.cancelled:
            return
        self.dbname = result["dbpath"]
        self.interface.update(
            self.dbname, self.user, self.password, self.host, self.port
        )


class PGMLNode(DBNode):
    node_color = monokai.GREEN
    interface: DBConnectionSingleton

    def __init__(
        self,
        flowchart: "Flowchart",
        center_x: float,
        center_y: float,
        label: str,
        **kwargs,
    ):
        self.interface = DBConnectionSingleton(PgMLInterface)
        super().__init__(flowchart, center_x, center_y, label, **kwargs)
        self.model = "gpt2-instruct-dolly"

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "dbname": self.dbname,
                "user": self.user,
                "password": self.password,
                "host": self.host,
                "port": self.port,
                "model": self.model,
            },
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        if self.options_popup.cancelled:
            return
        self.dbname = result["dbname"]
        self.user = result["user"]
        self.password = result["password"]
        self.host = result["host"]
        self.port = result["port"]  # maybe make an int?
        self.model = result["model"]
        self.interface.update(
            self.dbname, self.user, self.password, self.host, self.port
        )


class SQLiteQueryNode(DBNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, SQLiteInterface, **kwargs)

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        super().run_subclass(before_result, state, console)
        select = self.interface.interface.run_query(state.result)
        return str(select)

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "dbname": self.dbname,
            },
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        if self.options_popup.cancelled:
            return
        self.dbname = result["dbname"]
        self.interface.update(self.dbname)


class PGQueryNode(DBNode):
    def __init__(
        self,
        flowchart: "Flowchart",
        center_x: float,
        center_y: float,
        label: str,
        **kwargs,
    ):
        super().__init__(flowchart, center_x, center_y, label, PGInterface, **kwargs)

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        super().run_subclass(before_result, state, console)
        select = self.interface.interface.run_query(state.result)
        return str(select)


class PGGenerateNode(PGMLNode):
    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        super().run_subclass(before_result, state, console)
        gen = self.interface.interface.generate(self.model, state.result)[0][0]
        return gen
