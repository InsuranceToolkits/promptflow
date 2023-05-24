"""
Allow the user to edit application-wide options
"""
from promptflow.src.options import Options
from PyQt6.QtWidgets import QMainWindow

class AppOptions(QMainWindow):
    """
    Allow the user to edit application-wide options such as window size
    """

    def __init__(self, master, options: Options):
        super().__init__(master)
        self.options = options
        self.title("Promptflow Options")
        self.labels: dict[str, customtkinter.CTkLabel] = {}
        self.entries: dict[str, customtkinter.CTkEntry] = {}

        for index, (key, value) in enumerate(self.options.dict().items()):
            self.build_label_option(index, key, value)

        self.ok_button = customtkinter.CTkButton(self, text="OK", command=self.on_ok)
        self.ok_button.grid(row=2, column=0, padx=(10, 5), pady=(5, 5), sticky="e")
        self.cancel = customtkinter.CTkButton(
            self, text="Cancel", command=self.on_cancel
        )
        self.cancel.grid(row=2, column=1, padx=(5, 10), pady=(5, 5), sticky="w")
        self.grab_set()

    def build_label_option(self, index, label, value):
        """
        Create a label and entry for a given option
        """
        self.labels[label] = customtkinter.CTkLabel(self, text=label)
        self.labels[label].grid(
            row=index, column=0, padx=(10, 5), pady=(5, 5), sticky="e"
        )
        self.entries[label] = customtkinter.CTkEntry(self)
        self.entries[label].insert(0, value)
        self.entries[label].grid(
            row=index, column=1, padx=(5, 10), pady=(5, 5), sticky="w"
        )

    def on_ok(self):
        """
        Called when the user clicks the OK button
        """
        for key, entry in self.entries.items():
            setattr(self.options, key, entry.get())
        self.options.save("promptflow/options.json")
        self.destroy()

    def on_cancel(self):
        """
        Called when the user clicks the Cancel button
        """
        self.destroy()
