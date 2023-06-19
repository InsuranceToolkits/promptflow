from abc import ABC
import logging
from typing import Any, Callable, Optional, TYPE_CHECKING
from promptflow.src.db_interface.main import (
    PGInterface,
    PgMLInterface,
    SQLBase,
    SQLiteInterface,
)
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

    def run_subclass(self, before_result: Any, state) -> str:
        self.interface.interface.connect()
        return state.result

    def get_options(self) -> dict[str, Any]:
        base_options = super().get_options()
        base_options["options"]["dbname"] = self.dbname
        base_options["options"]["user"] = self.user
        base_options["options"]["password"] = self.password
        base_options["options"]["host"] = self.host
        base_options["options"]["port"] = self.port
        return base_options


class SQLiteNode(DBNode):
    node_color = monokai.GREEN

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.interface = DBConnectionSingleton(SQLiteInterface)


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

    def get_options(self) -> dict[str, Any]:
        base_options = super().get_options()
        base_options["options"]["model"] = self.model
        return base_options


class SQLiteQueryNode(DBNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, SQLiteInterface, **kwargs)

    def run_subclass(self, before_result: Any, state) -> str:
        super().run_subclass(before_result, state)
        select = self.interface.interface.run_query(state.result)
        return str(select)


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

    def run_subclass(self, before_result: Any, state) -> str:
        super().run_subclass(before_result, state)
        select = self.interface.interface.run_query(state.result)
        return str(select)


class PGGenerateNode(PGMLNode):
    def run_subclass(self, before_result: Any, state) -> str:
        super().run_subclass(before_result, state)
        gen = self.interface.interface.generate(self.model, state.result)[0][0]
        return gen
