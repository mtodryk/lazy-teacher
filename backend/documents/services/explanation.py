import logging

from .llm_client import AzureLlmClient
from .prompts import EXPLANATION_SYSTEM, EXPLANATION_USER, FOLLOWUP_SYSTEM

logger = logging.getLogger(__name__)

MAX_CHAT_MESSAGES = 20


def generate_explanation(
    question_text: str,
    correct_answer_text: str,
    source_chunks: list[str],
) -> str:
    context_text = (
        "\n---\n".join(source_chunks)
        if source_chunks
        else "Brak kontekstu z dokumentu."
    )

    llm = AzureLlmClient()
    user_prompt = EXPLANATION_USER.format(
        question=question_text,
        correct_answer=correct_answer_text,
        context=context_text,
    )

    response = llm.generate(
        system_prompt=EXPLANATION_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=600,
    )

    return response.content


def generate_followup(
    chat_history: list[dict],
    user_message: str,
) -> str:
    messages = [{"role": "system", "content": FOLLOWUP_SYSTEM}]

    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})

    llm = AzureLlmClient()
    response = llm.client.chat.completions.create(
        model=llm.deployment,
        messages=messages,
        temperature=0.3,
        max_tokens=600,
    )

    return response.choices[0].message.content.strip()
