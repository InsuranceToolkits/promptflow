from typing import TYPE_CHECKING, Any, Optional

import tiktoken
from PyQt6.QtWidgets import QTextEdit
from promptflow.src.state import State

from promptflow.src.text_data import TextData
from promptflow.src.utils import retry_with_exponential_backoff

if TYPE_CHECKING:
    from promptflow.src.flowchart import Flowchart
from promptflow.src.nodes.node_base import NodeBase
from promptflow.src.dialogues.text_input import TextInput
from promptflow.src.dialogues.node_options import NodeOptions
from promptflow.src.themes import monokai

import openai
import anthropic
import google.generativeai as genai
import os
import enum


class OpenAIModel(enum.Enum):
    # manually add these as they become available
    # https://platform.openai.com/docs/models
    textdavinci = "text-davinci-003"
    gpt35turbo = "gpt-3.5-turbo"
    gpt35turbo0301 = "gpt-3.5-turbo-0301"
    gpt4 = "gpt-4"
    gpt40314 = "gpt-4-0314"


class AnthropicModel(enum.Enum):
    claude_v1 = "claude-v1"
    claude_v1_100k = "claude-v1-100k"
    claude_instant_v1 = "claude-instant-v1"
    claude_instant_v1_100k = "claude-instant-v1-100k"


class GoogleModel(enum.Enum):
    text_bison_001 = "text-bison-001"
    chat_bison_001 = "chat-bison-001"


chat_models = [
    OpenAIModel.gpt35turbo.value,
    OpenAIModel.gpt35turbo0301.value,
    OpenAIModel.gpt4.value,
    OpenAIModel.gpt40314.value,
    GoogleModel.chat_bison_001.value,
]


# https://openai.com/pricing
prompt_cost_1k = {
    OpenAIModel.textdavinci.value: 0.02,
    OpenAIModel.gpt35turbo.value: 0.002,
    OpenAIModel.gpt35turbo0301.value: 0.002,
    OpenAIModel.gpt4.value: 0.03,
    OpenAIModel.gpt40314.value: 0.03,
    AnthropicModel.claude_instant_v1.value: 0.00163,
    AnthropicModel.claude_instant_v1_100k.value: 0.00163,
    AnthropicModel.claude_v1.value: 0.01102,
    AnthropicModel.claude_v1_100k.value: 0.01102,
    GoogleModel.text_bison_001.value: 0.001,
    GoogleModel.chat_bison_001.value: 0.0005,
}
completion_cost_1k = {
    OpenAIModel.textdavinci.value: 0.02,
    OpenAIModel.gpt35turbo.value: 0.002,
    OpenAIModel.gpt35turbo0301.value: 0.002,
    OpenAIModel.gpt4.value: 0.06,
    OpenAIModel.gpt40314.value: 0.06,
    AnthropicModel.claude_instant_v1.value: 0.00551,
    AnthropicModel.claude_instant_v1_100k.value: 0.00551,
    AnthropicModel.claude_v1.value: 0.03268,
    AnthropicModel.claude_v1_100k.value: 0.03268,
    GoogleModel.text_bison_001.value: 0.001,
    GoogleModel.chat_bison_001.value: 0.0005,
}


class OpenAINode(NodeBase):
    """
    Node that uses the OpenAI API to generate text.
    """

    node_color = monokai.GREEN

    def __init__(
        self,
        flowchart: "Flowchart",
        center_x: float,
        center_y: float,
        label: str,
        **kwargs,
    ):
        self.model = kwargs.get("model", OpenAIModel.gpt35turbo.value)
        self.temperature = kwargs.get("temperature", 0.0)
        self.top_p = kwargs.get("top_p", 1.0)
        self.n = kwargs.get("n", 1)
        self.max_tokens = kwargs.get("max_tokens", 256)
        self.presence_penalty = kwargs.get("presence_penalty", 0.0)
        self.frequency_penalty = kwargs.get("frequency_penalty", 0.0)

        self.model_var = tk.StringVar(value=self.model)
        super().__init__(flowchart, center_x, center_y, label, **kwargs)
        self.canvas.tag_bind(self.item, "<Double-Button-1>", self.edit_options)
        self.canvas.update()
        self.bind_drag()
        self.bind_mouseover()
        self.text_window: Optional[TextInput] = None
        self.options_popup: Optional[NodeOptions] = None

    def edit_options(self, event):
        """
        Create a menu to edit the prompt.
        """
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "Model": self.model_var.get(),
                "Temperature": self.temperature,
                "Top P": self.top_p,
                "n": self.n,
                # "stop": self.stop,
                "Max Tokens": self.max_tokens,
                "presence_penalty": self.presence_penalty,
                "frequency_penalty": self.frequency_penalty,
            },
            {
                "Model": [model.value for model in OpenAIModel],
            },
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        # check if cancel
        if self.options_popup.cancelled:
            return
        self.model_var.set(result["Model"])
        self.on_model_select(None)  # todo: manually calling this is a bit hacky
        self.max_tokens = int(result["Max Tokens"])
        self.temperature = float(result["Temperature"])
        self.top_p = float(result["Top P"])
        self.n = int(result["n"])
        # self.stop = result["stop"]
        self.presence_penalty = float(result["presence_penalty"])
        self.frequency_penalty = float(result["frequency_penalty"])

    @retry_with_exponential_backoff
    def _chat_completion(self, prompt: str, state: State) -> str:
        """
        Simple wrapper around the OpenAI API to generate text.
        """
        messages = [
            *state.history,
        ]
        if prompt:
            messages.append({"role": "user", "content": prompt})
        completion = openai.ChatCompletion.create(
            model=self.model_var.get(),
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            n=self.n,
            # stop=self.stop,
            max_tokens=self.max_tokens,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty,
        )
        return completion["choices"][0]["message"]["content"]  # type: ignore

    @retry_with_exponential_backoff
    def _completion(self, prompt: str, state: State) -> str:
        """
        Simple wrapper around the OpenAI API to generate text.
        """
        # todo this history is really opinionated
        history = "\n".join(
            [
                *[
                    f"{message['role']}: {message['content']}"
                    for message in state.history
                ],
            ]
        )
        prompt = f"{history}\n{prompt}\n"
        completion = openai.Completion.create(
            model=self.model_var.get(),
            prompt=prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            n=self.n,
            # stop=self.stop,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty,
        )
        return completion["choices"][0]["text"]  # type: ignore

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        """
        Format the prompt and run the OpenAI API.
        """
        openai.api_key = os.getenv("OPENAI_API_KEY")
        prompt = state.result
        self.logger.info(f"Running LLMNode with prompt: {prompt}")
        if self.model in chat_models:
            completion = self._chat_completion(prompt, state)
        else:
            completion = self._completion(prompt, state)
        self.logger.info(f"Result of LLMNode is {completion}")  # type: ignore
        return completion  # type: ignore

    def serialize(self):
        return super().serialize() | {
            "model": self.model_var.get(),
            "temperature": self.temperature,
            "top_p": self.top_p,
            "n": self.n,
            "max_tokens": self.max_tokens,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
        }

    def on_model_select(self, event):
        """
        Callback for when the OpenAI model is changed.
        """
        self.model = self.model_var.get()
        if self.model in [OpenAIModel.gpt4.value, OpenAIModel.gpt40314.value]:
            self.logger.warning("You're using a GPT-4 model. This is costly.")
        self.logger.info(f"Selected model: {self.model}")

    def cost(self, state: State) -> float:
        """
        Return the cost of running this node.
        """
        # count the number of tokens
        enc = tiktoken.encoding_for_model(self.model)
        prompt_tokens = enc.encode(state.result.format(state=state))
        max_completion_tokens = self.max_tokens - len(prompt_tokens)
        prompt_cost = prompt_cost_1k[self.model] * len(prompt_tokens) / 1000
        completion_cost = completion_cost_1k[self.model] * max_completion_tokens / 1000
        total = prompt_cost + completion_cost
        return total


class ClaudeNode(NodeBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = kwargs.get("model", AnthropicModel.claude_v1.value)
        self.model_var = tk.StringVar(value=self.model)
        self.max_tokens = kwargs.get("max_tokens", 256)

    def _build_history(self, state: State) -> str:
        history = ""
        for message in state.history:
            if message["role"] == "user":
                prompt = anthropic.HUMAN_PROMPT
            else:
                prompt = anthropic.AI_PROMPT
            history += f"{prompt}: {message['content']}\n"
        # finally add the current prompt
        history += f"{anthropic.HUMAN_PROMPT}: {state.result}\n"
        return history

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        """
        Format the prompt and run the Anthropics API
        """
        c = anthropic.Client(os.environ["ANTHROPIC_API_KEY"])
        resp = c.completion(
            prompt=self._build_history(state) + "\n" + anthropic.AI_PROMPT,
            stop_sequences=[anthropic.HUMAN_PROMPT],
            model=self.model,
            max_tokens_to_sample=self.max_tokens,
        )
        return resp["completion"]

    def serialize(self):
        return super().serialize() | {
            "model": self.model_var.get(),
            "max_tokens": self.max_tokens,
        }

    def edit_options(self, event):
        """
        Create a menu to edit the prompt.
        """
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "Model": self.model_var.get(),
                "Max Tokens": self.max_tokens,
            },
            {
                "Model": [model.value for model in AnthropicModel],
            },
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        # check if cancel
        if self.options_popup.cancelled:
            return
        self.model_var.set(result["Model"])
        self.model = self.model_var.get()
        self.max_tokens = int(result["Max Tokens"])

    def cost(self, state: State) -> float:
        """
        Return the cost of running this node.
        """
        # count the number of tokens
        enc = tiktoken.encoding_for_model(self.model)
        prompt_tokens = enc.encode(state.result.format(state=state))
        max_completion_tokens = self.max_tokens - len(prompt_tokens)
        prompt_cost = prompt_cost_1k[self.model] * len(prompt_tokens) / 1000
        completion_cost = completion_cost_1k[self.model] * max_completion_tokens / 1000
        total = prompt_cost + completion_cost
        return total


class GoogleVertexNode(NodeBase):
    """
    Call to Google's Generative AI
    """

    model = GoogleModel.text_bison_001.value

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = kwargs.get("model", GoogleModel.text_bison_001.value)
        self.model_var = tk.StringVar(value=self.model)

    def _build_history(self, state: State) -> list[str]:
        history = []
        for message in state.history:
            if message["role"] == "user":
                history.append("User: " + message["content"])
            else:
                history.append("AI: " + message["content"])
        return history

    def run_subclass(
        self, before_result: Any, state, console: QTextEdit
    ) -> str:
        genai.configure(api_key=os.environ["GENAI_API_KEY"])
        response = genai.chat(
            model=self.model, messages=self._build_history(state), prompt=state.result
        )
        return response.last

    def edit_options(self, event):
        """
        Create a menu to edit the prompt.
        """
        self.options_popup = NodeOptions(
            self.canvas,
            {
                "Model": self.model_var.get(),
            },
            {
                "Model": [model.value for model in GoogleModel],
            },
        )
        self.canvas.wait_window(self.options_popup)
        result = self.options_popup.result
        # check if cancel
        if self.options_popup.cancelled:
            return
        self.model_var.set(result["Model"])

    def serialize(self):
        return super().serialize() | {
            "model": self.model_var.get(),
        }

    def cost(self, state: State) -> float:
        """
        Return the cost of running this node.
        """
        # count the number of tokens
        enc = tiktoken.encoding_for_model(self.model)
        prompt_tokens = enc.encode(state.result.format(state=state))
        max_completion_tokens = 1024 - len(prompt_tokens)
        prompt_cost = prompt_cost_1k[self.model] * len(prompt_tokens) / 1000
        completion_cost = completion_cost_1k[self.model] * max_completion_tokens / 1000
        total = prompt_cost + completion_cost
        return total
