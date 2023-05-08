from enum import Enum
import customtkinter


class Role(Enum):
    """Three types of roles for openai chat"""

    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"


class HistoryEditor(customtkinter.CTkToplevel):
    """
    Allows the user to edit the history manually
    """

    def __init__(self, master, init_history: list[dict[str, str]]):
        super().__init__(master)
        self.title("Edit History")
        self.history = init_history
        self.entries = {}
        self.add_button = None
        self.save_button = None
        self.cancel_button = None
        self.buttons = [
            self.add_button,
            self.save_button,
            self.cancel_button,
        ]

        self.build_gui()

    def build_gui(self):
        for index, item in enumerate(self.history):
            self.add_entry(index)
        self.add_button = customtkinter.CTkButton(self, text="Add", command=self.add)
        self.add_button.grid(
            row=len(self.history), column=0, padx=(10, 5), pady=(10, 10), sticky="e"
        )
        self.save_button = customtkinter.CTkButton(self, text="Save", command=self.save)
        self.save_button.grid(
            row=len(self.history) + 1,
            column=0,
            padx=(10, 5),
            pady=(10, 10),
            sticky="e",
        )
        self.cancel_button = customtkinter.CTkButton(
            self, text="Cancel", command=self.cancel
        )
        self.cancel_button.grid(
            row=len(self.history) + 1,
            column=1,
            padx=(10, 5),
            pady=(10, 10),
            sticky="e",
        )

    def add(self):
        """
        Add a new item to the history
        """
        self.history.append({"role": "user", "content": ""})
        self.add_entry(len(self.history) - 1)

    def delete(self, index):
        """
        Delete an item from the history
        """
        for entry in self.entries[index]:
            entry.destroy()

    def save(self):
        """
        Save the edit
        """
        self.history = []
        for index, entry in self.entries.items():
            self.history.append({"role": entry[0].get(), "content": entry[1].get()})
        self.destroy()

    def cancel(self):
        """
        Cancel the edit
        """
        self.destroy()

    def add_entry(self, index):
        role = customtkinter.CTkComboBox(self, values=[role.value for role in Role])
        role.grid(row=index, column=0, padx=(10, 5), pady=(5, 5), sticky="e")

        content = customtkinter.CTkEntry(self)
        content.grid(row=index, column=1, padx=(5, 10), pady=(5, 5), sticky="w")
        content.insert(0, self.history[index]["content"])

        delete_button = customtkinter.CTkButton(
            self, text="Delete", command=lambda index=index: self.delete(index)
        )
        delete_button.grid(row=index, column=2, padx=(5, 10), pady=(5, 5), sticky="w")

        self.entries[index] = [role, content, delete_button]

        self.add_button.grid_forget()
        self.add_button.grid(
            row=len(self.history), column=0, padx=(10, 5), pady=(10, 10), sticky="e"
        )
        self.save_button.grid_forget()
        self.save_button.grid(
            row=len(self.history) + 1,
            column=0,
            padx=(10, 5),
            pady=(10, 10),
            sticky="e",
        )
        self.cancel_button.grid_forget()
        self.cancel_button.grid(
            row=len(self.history) + 1,
            column=1,
            padx=(10, 5),
            pady=(10, 10),
            sticky="e",
        )
