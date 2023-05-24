"""
Displays a cursor on the canvas.
"""

from promptflow.src.themes import monokai
from PyQt6.QtGui import QPixmap, QPainter


class FlowchartCursor:
    size_px = 10
    width = 2

    def __init__(
        self, canvas: QPixmap, center_x: float = 0, center_y: float = 0
    ) -> None:
        self.canvas = canvas
        self.center_x = center_x
        self.center_y = center_y
        self.draw()

    def draw(self):
        """
        Draw a plus sign on the canvas.
        """
        painter = QPainter(self.canvas)
        painter.setPen(int(monokai.COMMENTS.strip("#"), 16))
        painter.setBrush(int(monokai.COMMENTS.strip("#"), 16))
        painter.drawLine(
            int(self.center_x - self.size_px / 2),
            int(self.center_y),
            int(self.center_x + self.size_px / 2),
            int(self.center_y),
        )
        painter.drawLine(
            int(self.center_x),
            int(self.center_y - self.size_px / 2),
            int(self.center_x),
            int(self.center_y + self.size_px / 2),
        )


    def move_to(self, new_x: float, new_y: float):
        """
        Clear the icon and draw a new cursor at the new location.
        """
        self.center_x = new_x
        self.center_y = new_y
        self.clear()
        self.draw()

    def clear(self):
        """
        Clear the cursor from the canvas.
        """
        self.canvas.delete("cursor")
