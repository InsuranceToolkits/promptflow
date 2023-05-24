"""
Simple text input dialogue.
"""
from typing import Callable, TYPE_CHECKING, Optional
from PyQt6.QtWidgets import QMainWindow, QTextEdit
from promptflow.src.text_data import TextData

if TYPE_CHECKING:
    from promptflow.src.flowchart import Flowchart


class TextInput(QMainWindow):
    """
    A basic text editor for editing TextData
    """

    def __init__(
        self,
        parent,
        flowchart: "Flowchart",
        text_data: Optional[TextData | dict] = None,
    ):
        super().__init__(parent)

        self.flowchart = flowchart
        if text_data is None:
            text_data = {"label": "", "text": ""}
        if isinstance(text_data, dict):
            text_data = TextData.deserialize(text_data, flowchart)

        self.text_data = text_data

        self.modified = False
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.title(self.text_data.label)

        self.text_select_label = customtkinter.CTkLabel(self, text="Text data:")
        self.text_select_label.pack()
        self.text_select_dropdown = customtkinter.CTkComboBox(
            self,
            values=list(self.flowchart.text_data_registry.keys()),
            state="readonly",
            command=self.on_text_data_select,
        )
        self.text_select_dropdown.set(self.text_data.label)
        self.text_select_dropdown.pack()

        self.label_entry_label = customtkinter.CTkLabel(self, text="Label:")
        self.label_entry_label.pack()
        self.label_entry = customtkinter.CTkEntry(self)
        self.label_entry.pack()

        self.text_entry = customtkinter.CTkTextbox(self, width=400, height=400)
        self.text_entry.pack(fill=tk.BOTH, expand=True)

        # save, open, export, cancel
        self.menu = tk.Menu(self)
        self.file_menu = tk.Menu(self.menu, tearoff=0)
        self.file_menu.add_command(
            label="Save Node", command=self.save, accelerator="Ctrl+S"
        )
        self.file_menu.add_command(
            label="Import File", command=self.read_file, accelerator="Ctrl+O"
        )
        self.file_menu.add_command(
            label="Export File", command=self.export_text, accelerator="Ctrl+E"
        )
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Cancel", command=self.destroy)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.config(menu=self.menu)

        # register keyboard shortcuts
        self.bind("<Control-s>", lambda event: self.save())
        self.bind("<Control-o>", lambda event: self.read_file())
        self.bind("<Control-e>", lambda event: self.export_text())

        self.label_entry.insert(0, self.text_data.label)
        self.text_entry.insert("1.0", self.text_data.text)
        # on label change, update title
        self.text_entry.bind("<KeyRelease>", self.on_text_modified)
        self.label_entry.bind("<KeyRelease>", self.on_label_modified)
        self.callback = lambda: None
        self.grab_set()

    def get_text(self) -> TextData:
        """
        Create a new TextData object from the current state of the dialogue.
        """
        return TextData(
            self.label_entry.get(), self.text_entry.get("1.0", "end"), self.flowchart
        )

    def set_text(self, text: str):
        """
        Insert text into the text entry and updates the textdata model.
        """
        self.text_entry.delete("1.0", "end")
        self.text_entry.insert("1.0", text)
        self.text_data.text = text

    def set_label(self, label: str):
        """
        Insert a label into the label entry and updates the textdata model.
        """
        self.title(label)
        self.label_entry.delete(0, "end")
        self.label_entry.insert(0, label)
        self.text_data.label = label

    def set_callback(self, callback: Callable):
        """
        Sets the callback function to be called when the save button is pressed.
        """
        self.callback = callback

    def on_text_modified(self, _):
        """
        Set the modified flag to True when the text entry is modified.
        """
        self.modified = True
        self.title(self.label_entry.get() + " *")

    def on_label_modified(self, _):
        """
        Set the modified flag to True when the label entry is modified.
        """
        self.modified = True
        self.title(self.label_entry.get() + " *")

    def save(self):
        """
        Save the current text data to the node and close the dialogue.
        """
        # force a textdata update (kidna ugly)
        self.text_data.text = self.text_entry.get("1.0", "end")
        self.text_data.label = self.label_entry.get()
        self.flowchart.register_text_data(self.text_data)
        self.callback()
        self.modified = False
        self.destroy()

    def read_file(self):
        """
        Import a file into the text entry.
        """
        file_path = tkinter.filedialog.askopenfilename()
        if not file_path:
            return
        label = file_path.split("/")[-1]
        with open(file_path, "r", encoding="utf-8") as file:
            self.text_data = TextData(label, file.read(), self.flowchart)
        self.set_text(self.text_data.text)
        self.set_label(self.text_data.label)

    def export_text(self):
        """
        Write the text entry to a file.
        """
        file_path = tkinter.filedialog.asksaveasfilename(
            initialfile=self.text_data.label
        )
        if not file_path:
            return
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(self.text_entry.get("1.0", "end"))

    def on_text_data_select(self, _):
        """
        When a text data is selected from the dropdown, update the text entry
        and label
        """
        self.text_data = self.flowchart.text_data_registry[
            self.text_select_dropdown.get()
        ].copy(self.flowchart)
        self.set_text(self.text_data.text)
        self.set_label(self.text_data.label)

    def on_close(self):
        """
        Check for unsaved changes before closing the window.
        """
        if self.modified:
            result = tkinter.messagebox.askyesnocancel(
                "Unsaved changes",
                "There are unsaved changes. Do you want to save them before closing?",
            )

            if result is None:  # Cancel was pressed
                return
            elif result:  # Yes was pressed
                self.save()
            else:  # No was pressed
                self.destroy()
        else:
            self.destroy()
