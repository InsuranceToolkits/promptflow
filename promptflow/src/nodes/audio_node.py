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
from promptflow.src.nodes.node_base import NodeBase
from promptflow.src.state import State
from promptflow.src.text_data import TextData

key = os.getenv("ELEVENLABS_API_KEY")
if key:
    elevenlabs.set_api_key(key)


class AudioNode(NodeBase, ABC):
    """
    Base class for handling audio
    """


class AudioInputNode(AudioNode, ABC):
    """
    Node for recording audio
    """

    data: Optional[list[float]] = None

    def before(self, state: State) -> Any:
        """
        Todo: Tell gui to get voice data
        """

    def run_subclass(self, before_result: Any, state) -> str:
        return state.result


class AudioOutputNode(AudioNode, ABC):
    """
    Node that plays back audio in some way
    """


class WhispersNode(AudioInputNode):
    """
    Uses OpenAI's Whispers API to transcribe audio
    """

    prompt: TextData
    filename: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt = kwargs.get(
            "prompt", TextData("Whisper Prompt", "", self.flowchart)
        )

    def run_subclass(self, before_result: Any, state) -> str:
        super().run_subclass(before_result, state)
        transcript = openai.Audio.translate("whisper-1", open(self.filename, "rb"))
        return transcript["text"]

    def cost(self, state):
        price_per_minute = 0.006
        # get length of file in minutes
        with wave.open(self.filename, "rb") as wav_file:
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

    def get_options(self) -> dict[str, Any]:
        base_options = super().get_options()
        base_options["options"].update(
            {
                "prompt": self.prompt,
            }
        )
        base_options["editor"] = "text"
        return base_options


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

    def run_subclass(self, before_result: Any, state) -> str:
        audio = elevenlabs.generate(
            text=state.result, voice="Bella", model="eleven_monolingual_v1"
        )
        elevenlabs.play(audio)
        return state.result

    def serialize(self):
        return super().serialize() | {
            "voice": self.voice,
            "model": self.model,
        }

    def cost(self, state):
        # overage is $0.30 per 1000 characters
        return 0.30 * len(state.result) / 1000

    def get_options(self) -> dict[str, Any]:
        base_options = super().get_options()
        base_options["options"].update(
            {
                "voice": self.voice,
                "model": self.model,
            }
        )
        base_options["editor"] = "text"
        return base_options
