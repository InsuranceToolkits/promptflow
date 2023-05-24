"""
Handles all audio-related nodes
"""
from abc import ABC
import os
from typing import Any, Optional
import wave
import openai
import elevenlabs
import numpy as np
import sounddevice as sd
from PyQt6.QtWidgets import QMainWindow, QTextEdit
from promptflow.src.dialogues.node_options import NodeOptions
from promptflow.src.dialogues.text_input import TextInput
from promptflow.src.nodes.node_base import NodeBase
from promptflow.src.state import State
from promptflow.src.text_data import TextData

key = os.getenv("ELEVENLABS_API_KEY")
if key:
    elevenlabs.set_api_key(key)


class AudioInputInterface(QMainWindow):
    """
    Popup window for recording audio
    """

    def __init__(self, master):
        super().__init__(master)
        self.title("Audio Input")
        self.recording = False
        self.audio_data = []
        self.filename = "out.wav"
        self.elapsed_time = 0

        self.time_label = customtkinter.CTkLabel(self, text="0:00")
        self.time_label.pack(pady=10, padx=10)

        self.start_button = customtkinter.CTkButton(
            self, text="Start", command=self.start
        )
        self.start_button.pack(pady=10, padx=10)

        self.stop_button = customtkinter.CTkButton(self, text="Stop", command=self.stop)
        self.stop_button.pack(padx=10)

        self.playback_button = customtkinter.CTkButton(
            self, text="Playback", command=self.playback
        )
        self.playback_button.pack(pady=10, padx=10)

        self.continue_button = customtkinter.CTkButton(
            self, text="Continue", command=self.destroy
        )
        self.continue_button.pack(pady=10, padx=10)

    def start(self):
        """
        Start recording audio
        """
        if not self.recording:
            self.recording = True
            self.audio_data = []
            self.start_button.configure(text="Recording...")
            self.update_timer()
            self.record()

    def update_timer(self):
        """
        Update timer label
        """
        if self.recording:
            self.elapsed_time += 1
            minutes, seconds = divmod(self.elapsed_time, 60)
            self.time_label.configure(text=f"{minutes}:{seconds:02d}")
            self.master.after(1000, self.update_timer)

    def record(self):
        """
        Record audio in 1-second chunks
        """
        if self.recording:
            duration = 1  # Record in 1-second chunks
            sample_rate = 44100
            device_info = sd.query_devices(sd.default.device, "input")
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=device_info["max_input_channels"] // 32,
                dtype="int16",
                blocking=True,
            )
            sd.wait()
            self.audio_data.append(recording)

            # Continue recording until stopped
            self.master.after(1, self.record)

    def stop(self):
        """
        Finish recording audio and save to file
        """
        if self.recording:
            self.recording = False
            self.start_button.configure(text="Start")

            # Save the audio data to a file
            with wave.open(self.filename, "wb") as wavefile:
                sample_rate = 44100
                wavefile.setnchannels(2)
                wavefile.setsampwidth(2)
                wavefile.setframerate(sample_rate)
                wavefile.writeframes(np.concatenate(self.audio_data).tobytes())

    def playback(self):
        """
        Play back the audio file
        """
        if not self.recording:
            with wave.open(self.filename, "rb") as wf:
                sample_rate = wf.getframerate()
                audio_data = np.frombuffer(
                    wf.readframes(wf.getnframes()), dtype="int32"
                )
                sd.play(audio_data, samplerate=sample_rate, blocking=True)


class AudioNode(NodeBase, ABC):
    """
    Base class for handling audio
    """


class AudioInputNode(AudioNode, ABC):
    """
    Node for recording audio
    """

    audio_input_interface: Optional[AudioInputInterface] = None
    data: Optional[list[float]] = None

    def before(self, state: State, console: QTextEdit) -> Any:
        self.audio_input_interface = AudioInputInterface(self.canvas)
        self.canvas.wait_window(self.audio_input_interface)
        self.data = self.audio_input_interface.audio_data

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        return state.result


class AudioOutputNode(AudioNode, ABC):
    """
    Node that plays back audio in some way
    """

    options_popup: Optional[NodeOptions] = None


class WhispersNode(AudioInputNode):
    """
    Uses OpenAI's Whispers API to transcribe audio
    """

    prompt: TextData
    options_popup: Optional[NodeOptions] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt = kwargs.get(
            "prompt", TextData("Whisper Prompt", "", self.flowchart)
        )
        self.prompt_item = self.canvas.create_text(
            self.center_x,
            self.center_y + 30,
            text=self.prompt.label,
            fill="black",
            width=self.size_px * 2,
            justify="center",
        )
        self.items.extend([self.prompt_item])
        self.canvas.tag_bind(self.prompt_item, "<Double-Button-1>", self.edit_options)
        self.text_window: Optional[TextInput] = None
        self.bind_drag()
        self.bind_mouseover()

    def edit_options(self, event):
        self.text_window = TextInput(self.canvas, self.flowchart, self.prompt)
        self.text_window.set_callback(self.save_prompt)

    def save_prompt(self):
        """
        Write the prompt to the canvas.
        """
        if self.text_window is None:
            self.logger.warning("No text window to save")
            return
        self.prompt = self.text_window.get_text()
        self.canvas.itemconfig(self.prompt_item, text=self.prompt.label)
        self.text_window.destroy()

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        super().run_subclass(before_result, state, console)
        transcript = openai.Audio.translate(
            "whisper-1", open(self.audio_input_interface.filename, "rb")
        )
        return transcript["text"]

    def cost(self, state):
        if not self.audio_input_interface:
            return 0
        price_per_minute = 0.006
        # get length of file in minutes
        with wave.open(self.audio_input_interface.filename, "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            audio_data = np.frombuffer(
                wav_file.readframes(wav_file.getnframes()), dtype="int32"
            )
            duration = len(audio_data) / sample_rate
            return duration / 60 * price_per_minute

    def serialize(self):
        return super().serialize() | {
            "prompt": self.prompt.serialize(),
        }


class ElevenLabsNode(AudioOutputNode):
    """
    Uses ElevenLabs API to generate realistic speech
    """

    voice: str = "Bella"
    model: str = "eleven_monolingual_v1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.voice = kwargs.get("voice", self.voice)
        self.model = kwargs.get("model", self.model)

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        audio = elevenlabs.generate(
            text=state.result, voice="Bella", model="eleven_monolingual_v1"
        )
        elevenlabs.play(audio)
        return state.result

    def edit_options(self, event):
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "Voice": self.voice,
                "Model": self.model,
            },
        )
        self.canvas.wait_window(self.options_popup)
        if self.options_popup.cancelled:
            return
        self.voice = self.options_popup.result["Voice"]
        self.model = self.options_popup.result["Model"]

    def serialize(self):
        return super().serialize() | {
            "voice": self.voice,
            "model": self.model,
        }

    def cost(self, state):
        # overage is $0.30 per 1000 characters
        return 0.30 * len(state.result) / 1000
