"""
LLM service — wraps OpenAI chat completions.

Loads the system prompt from the assistant's prompt.md file so prompts
live in plain text and are easy to iterate without touching Python.
"""
import logging
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from app.core.config import ASSISTANTS_DIR, get_settings

logger = logging.getLogger("jamiiz.llm")

_PROMPT_CACHE: dict[str, str] = {}


def load_prompt(assistant_type: str) -> str:
    """Load and cache the system prompt for an assistant type."""
    if assistant_type in _PROMPT_CACHE:
        return _PROMPT_CACHE[assistant_type]

    path = ASSISTANTS_DIR / assistant_type / "prompt.md"
    if not path.exists():
        raise FileNotFoundError(f"No prompt found for assistant: {assistant_type!r} at {path}")

    prompt = path.read_text(encoding="utf-8")
    _PROMPT_CACHE[assistant_type] = prompt
    logger.debug("Loaded prompt for assistant: %s (%d chars)", assistant_type, len(prompt))
    return prompt


class LLMService:
    def __init__(self) -> None:
        settings = get_settings()
        self._llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.2,
            api_key=settings.openai_api_key,
        )
        self._parser = StrOutputParser()

    def chat(
        self,
        assistant_type: str,
        user_message: str,
        context: str = "",
        history: list[dict] | None = None,
    ) -> str:
        """
        Single-turn chat with optional RAG context injected into the prompt.

        Args:
            assistant_type: one of 'website', 'property', 'document'
            user_message:   the user's question
            context:        retrieved chunks (pre-formatted as a string)
            history:        list of {"role": "user"|"assistant", "content": "..."}
        """
        system_prompt = load_prompt(assistant_type)

        if context:
            system_prompt += f"\n\n---\nRELEVANT CONTEXT:\n{context}\n---"

        messages: list = [SystemMessage(content=system_prompt)]

        if history:
            from langchain_core.messages import AIMessage
            for turn in history[-6:]:  # keep last 3 exchanges
                if turn["role"] == "user":
                    messages.append(HumanMessage(content=turn["content"]))
                elif turn["role"] == "assistant":
                    messages.append(AIMessage(content=turn["content"]))

        messages.append(HumanMessage(content=user_message))

        chain = self._llm | self._parser
        response = chain.invoke(messages)
        logger.debug("LLM response length: %d chars", len(response))
        return response

    @property
    def llm(self) -> ChatOpenAI:
        """Expose raw LLM for use in LangGraph nodes."""
        return self._llm


_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
