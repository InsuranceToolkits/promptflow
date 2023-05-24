"""
Tkinter class for a multi file input, where the user can 
specify how many files with a browse field can be specified.
"""
from tkinter import filedialog
from PyQt6.QtWidgets import QMainWindow


class MultiFileInput(QMainWindow):
    def __init__(self, master, fields: dict[str, str]):
        super().__init__(master)
        self.title("Add Files")
        self.fields = fields
        self.result = {}
        self.entries = {}

        for index, field in enumerate(self.fields):
            label = customtkinter.CTkLabel(self, text=field)
            label.grid(row=index, column=0, padx=(10, 5), pady=(5, 5), sticky="e")

            entry = customtkinter.CTkEntry(self)
            entry.grid(row=index, column=1, padx=(5, 10), pady=(5, 5), sticky="w")
            self.entries[field] = entry
            entry.insert(0, self.fields.get(field, ""))

            browse_button = customtkinter.CTkButton(
                self, text="Browse", command=lambda field=field: self.browse(field)
            )
            browse_button.grid(
                row=index, column=2, padx=(5, 10), pady=(5, 5), sticky="w"
            )

        save_button = customtkinter.CTkButton(self, text="Save", command=self.save)
        save_button.grid(
            row=len(self.fields),
            column=0,
            padx=(10, 5),
            pady=(10, 10),
            sticky="e",
        )

        cancel_button = customtkinter.CTkButton(
            self, text="Cancel", command=self.cancel
        )
        cancel_button.grid(
            row=len(self.fields),
            column=1,
            padx=(5, 10),
            pady=(10, 10),
            sticky="w",
        )

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.cancelled = False
        self.grab_set()

    def browse(self, field):
        """
        Browse for a file
        """
        filename = filedialog.askopenfilename()
        self.entries[field].delete(0, tk.END)
        self.entries[field].insert(0, filename)

    def save(self):
        """
        Write the values from the entries back to the result dict
        """
        for key, entry in self.entries.items():
            self.result[key] = entry.get()
        self.destroy()

    def cancel(self):
        """
        Cancel the editing, setting the flag
        """
        self.cancelled = True
        self.destroy()
