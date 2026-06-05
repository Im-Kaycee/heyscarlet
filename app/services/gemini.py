import google.generativeai as genai
from typing import AsyncGenerator, List, Dict
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)


def _build_history(messages: List[Dict]) -> List[Dict]:
    """
    Convert stored messages into Gemini chat history format.
    messages: list of {"role": "user"|"assistant", "content": "..."}
    """
    history = []
    for msg in messages:
        # Gemini uses "model" not "assistant"
        role = "model" if msg["role"] == "assistant" else "user"
        history.append({"role": role, "parts": [msg["content"]]})
    return history


async def stream_scarlet_response(
    user_message: str,
    history: List[Dict],
    memory_context: str = "",
) -> AsyncGenerator[str, None]:
    """
    Stream Scarlet's response token by token via Gemini.

    Args:
        user_message: the current user input
        history: prior messages in this conversation
        memory_context: injected user memory string for context
    """
    system_prompt = settings.SCARLET_SYSTEM_PROMPT
    if memory_context:
        system_prompt += f"\n\nWhat you know about this user:\n{memory_context}"

    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=system_prompt,
    )

    chat = model.start_chat(history=_build_history(history))

    response = await chat.send_message_async(user_message, stream=True)

    async for chunk in response:
        if chunk.text:
            yield chunk.text