"""
Handles image data
"""
from abc import ABC
import base64
from enum import Enum
from PIL import Image, ImageTk
import json
import io
from typing import Any
import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from PyQt6.QtWidgets import QTextEdit


from promptflow.src.dialogues.image_inspector import ImageInspector
from promptflow.src.dialogues.node_options import NodeOptions
from promptflow.src.nodes.node_base import NodeBase

import openai


class ImageSize(Enum):
    """
    Image sizes
    """

    s256x256 = "256x256"
    s512x512 = "512x512"
    s1024x1024 = "1024x1024"


class ImageNode(NodeBase, ABC):
    """
    Base class for image nodes
    """

    pass


class OpenImageFile(ImageNode):
    """
    Specify a file to open
    """

    filename = ""

    def edit_options(self, event):
        options_popup = NodeOptions(
            self.canvas,
            {
                "filename": self.filename,
            },
            file_options={"filename": self.filename},
        )
        self.canvas.wait_window(options_popup)
        if options_popup.cancelled:
            return
        self.filename = options_popup.result["filename"]

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        # convert tkphotoimage to PIL image
        pil_image = Image.open(self.filename)
        self.image = ImageTk.PhotoImage(pil_image)
        self.image_inspector = ImageInspector(self.canvas, self.image)
        self.canvas.wait_window(self.image_inspector)
        state.data = self.image
        return state.result


class JSONImageFile(ImageNode):
    """
    Open a file specified by input JSON
    """

    filename_key: str = "filename"
    options_popup: NodeOptions

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.filename_key = kwargs.get("filename_key", "")

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "filename_key": self.filename_key,
            },
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        # check if cancel
        if self.options_popup.cancelled:
            return
        self.filename_key = result["filename_key"]

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        try:
            data = json.loads(state.result)
        except json.decoder.JSONDecodeError:
            return "Invalid JSON"
        # convert tkphotoimage to PIL image
        pil_image = Image.open(data[self.filename_key])
        self.image = ImageTk.PhotoImage(pil_image)
        self.image_inspector = ImageInspector(self.canvas, self.image)
        self.canvas.wait_window(self.image_inspector)
        state.data = self.image
        return state.result

    def serialize(self) -> dict[str, Any]:
        return super().serialize() | {
            "filename_key": self.filename_key,
        }


class DallENode(ImageNode):
    """
    Call OpenAI's Dall-E API
    """

    n = 1
    size = ImageSize.s256x256.value
    image = None

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        response = openai.Image.create(
            prompt=state.result,
            n=int(self.n),
            size=self.size,
            response_format="b64_json",
        )
        # show the image
        imgdata = base64.b64decode(response["data"][0]["b64_json"])
        pil_image = Image.open(io.BytesIO(imgdata))
        self.image = ImageTk.PhotoImage(pil_image)
        self.image_inspector = ImageInspector(self.canvas, self.image)
        self.canvas.wait_window(self.image_inspector)
        state.data = self.image
        return state.result

    def edit_options(self, event):
        options_popup = NodeOptions(
            self.canvas,
            {
                "n": self.n,
                "size": self.size,
            },
            {
                "size": [size.value for size in ImageSize],
            },
        )
        self.canvas.wait_window(options_popup)
        if options_popup.cancelled:
            return
        self.n = int(options_popup.result["n"])
        self.size = options_popup.result["size"]

    def serialize(self) -> dict[str, Any]:
        return super().serialize() | {
            "n": self.n,
            "size": self.size,
        }


class CaptionNode(ImageNode):
    """
    Caption an image
    """

    max_length = 50

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        checkpoint = "microsoft/git-base"
        processor = AutoProcessor.from_pretrained(checkpoint)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # convert tkphotoimage to PIL image
        pil_image = ImageTk.getimage(state.data)
        inputs = processor(images=pil_image, return_tensors="pt").to(device)
        pixel_values = inputs.pixel_values
        model = AutoModelForCausalLM.from_pretrained(checkpoint)
        generated_ids = model.generate(
            pixel_values=pixel_values, max_length=int(self.max_length)
        )
        generated_caption = processor.batch_decode(
            generated_ids, skip_special_tokens=True
        )[0]
        return generated_caption

    def edit_options(self, event):
        options_popup = NodeOptions(
            self.canvas,
            {
                "max_length": self.max_length,
            },
        )
        self.canvas.wait_window(options_popup)
        if options_popup.cancelled:
            return
        self.max_length = int(options_popup.result["max_length"])

    def serialize(self) -> dict[str, Any]:
        return super().serialize() | {
            "max_length": self.max_length,
        }


class SaveImageNode(ImageNode):
    """
    Save image to filename
    """

    filename: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = kwargs.get("filename", "")

    def edit_options(self, event):
        options_popup = NodeOptions(
            self.canvas,
            {
                "filename": self.filename,
            },
            file_options={"filename": self.filename},
        )
        self.canvas.wait_window(options_popup)
        if options_popup.cancelled:
            return
        self.filename = options_popup.result["filename"]

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        # convert tkphotoimage to PIL image
        pil_image = ImageTk.getimage(state.data)
        pil_image.save(self.filename)
        return state.result

    def serialize(self) -> dict[str, Any]:
        return super().serialize() | {
            "filename": self.filename,
        }
