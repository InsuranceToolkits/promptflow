"""
Display image in a dialogue box
"""

from PIL import Image, ImageTk
from PyQt6.QtWidgets import QMainWindow



class ImageInspector(QMainWindow):
    """
    Displays an image in a dialogue box
    """

    def __init__(self, master, image: ImageTk.PhotoImage):
        super().__init__(master)
        self.master = master
        self.image = image
        self.title("Image Inspector")
        self.body()

    def body(self):
        self.canvas = customtkinter.CTkCanvas(
            self, width=self.image.width(), height=self.image.height()
        )
        self.canvas.pack()
        self.canvas.create_image(0, 0, image=self.image, anchor="nw")
        self.canvas.update()
        self.grab_set()

    def buttonbox(self):
        pass

    def destroy(self):
        super().destroy()
        self.image = None
