import json
import logging
import random
from itertools import cycle

from django.conf import settings
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Jesteś ekspertem światowej klasy w wyodrębnianiu kluczowych tematów z dokumentów.\n"
    "Twoim zadaniem jest przeanalizowanie CAŁEGO dokumentu i wybranie TYLKO najważniejszych, "
    "centralnych i najbardziej reprezentatywnych tematów, które tworzą rdzeń dokumentu.\n\n"
    "Zasady (przestrzegaj ich ściśle):\n"
    "- Liczba tematów NIE jest z góry ustalona – ma być dokładnie taka, jaka wynika z treści PDF-a "
    "(dla prostego dokumentu może być 3–4, dla bardzo złożonego nawet 8–12 – nigdy nie wymuszaj stałej liczby).\n"
    "- Wyodrębniaj TYLKO główne tematy (te, które pojawiają się w wielu miejscach i mają największy wpływ na całość).\n"
    "- Zupełnie ignoruj drobiazgi, przykłady, detale, statystyki, podpunkty, pojedyncze wzmianki, marginesowe kwestie.\n"
    "- Każda tematyka to krótka fraza (maks. 8–10 słów).\n"
    "- Tematy muszą być w języku polskim.\n"
    "- Żadnych duplikatów ani nakładających się tematów.\n"
    "- Posortuj według ważności (najważniejszy jako pierwszy).\n"
    "- Nigdy nie dodawaj wyjaśnień, opisów ani żadnego innego tekstu – wyłącznie czysty JSON."
)

USER_PROMPT_TEMPLATE = (
    "Oto cały dokument podzielony na fragmenty. Przeanalizuj CAŁY dokument jako całość "
    "i wyodrębnij dokładnie tyle głównych tematów, ile naprawdę zawiera PDF.\n\n"
    "<document>\n"
    "{combined_chunks}\n"
    "</document>\n\n"
    "Pamiętaj:\n"
    "- Nie ustalaj z góry żadnej liczby tematów.\n"
    "- Pomijaj całkowicie wszelkie drobiazgi i detale.\n"
    "- Zwróć odpowiedź ŚCIŚLE w poniższym formacie JSON i nic poza tym:\n\n"
    "{{\n"
    '  "topics": [\n'
    '    "Temat 1 – najważniejszy",\n'
    '    "Temat 2",\n'
    "    ...\n"
    '    "Temat n"\n'
    "  ]\n"
    "}}"
)


QUIZ_SYSTEM_PROMPT = (
    "Jesteś ekspertem od tworzenia bardzo wysokiej jakości pytań testowych na poziomie eksperckim (C1/C2).\n"
    "Pytania muszą być oparte wyłącznie na podanym kontekście z dokumentu.\n"
    "Zasady ściśle:\n"
    "- Dokładnie 1 poprawna odpowiedź\n"
    "- 3 wiarygodne, ale błędne distraktory (nie oczywiste, nie głupie)\n"
    "- Pytanie po polsku, profesjonalne, precyzyjne\n"
    "- Bez 'żaden z powyższych', 'wszystkie powyższe', 'nie wiem' itp.\n"
    "- Zwróć TYLKO czysty JSON, nic więcej."
)

QUIZ_USER_PROMPT_TEMPLATE = (
    'Temat: "{topic}"\n\n'
    "Kontekst z oryginalnego dokumentu (bardzo ważne):\n"
    "<context>\n"
    "{context}\n"
    "</context>\n\n"
    "{no_context_note}\n\n"
    "Wygeneruj dokładnie JEDNO pytanie wielokrotnego wyboru (4 opcje):\n"
    "Zwróć TYLKO czysty JSON w formacie:\n"
    "{{\n"
    '  "question": "pełne pytanie?",\n'
    '  "options": ["A. opcja1", "B. opcja2", "C. opcja3", "D. opcja4"],\n'
    '  "correct_index": 0\n'
    "}}\n"
    "correct_index = numer poprawnej opcji (0-3)"
)


def _get_client() -> AzureOpenAI:
    endpoint = settings.AZURE_OPENAI_ENDPOINT
    api_key = settings.AZURE_OPENAI_API_KEY

    if not endpoint or not api_key:
        raise ValueError(
            "Azure OpenAI credentials not configured. "
            "Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables."
        )

    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )


def extract_topics(chunks: list[str]) -> list[str]:
    response = _get_client().chat.completions.create(
        model=settings.AZURE_OPENAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    combined_chunks="\n\n".join(chunks)
                ),
            },
        ],
        temperature=0.0,
        max_tokens=800,
    )

    return _parse_topics(response.choices[0].message.content.strip())


def _parse_topics(raw: str) -> list[str]:
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        raw = "\n".join(lines)

    data = json.loads(raw)

    if not isinstance(data, dict) or "topics" not in data:
        raise ValueError("Response JSON missing 'topics' key")

    topics = data["topics"]
    if not isinstance(topics, list) or not all(isinstance(t, str) for t in topics):
        raise ValueError("'topics' must be a list of strings")

    return topics


def generate_rag_quiz(
    topics: list[str],
    count: int,
    collection,
    max_distance: float = 0.5,
    chunks_per_question: int = 3,
) -> list[dict]:
    """
    Generuje dokładnie 'count' pytań z 4 opcjami (1 poprawna).
    Każde pytanie jest oparte na rzeczywistych chunkach z ChromaDB (distance < 0.5).
    Jeśli nie ma dobrych chunków → LLM dostaje informację i może użyć wiedzy ogólnej.
    """
    quiz = []
    topic_cycle = cycle(topics)

    client = _get_client()

    for i in range(count):
        topic = next(topic_cycle)

        # 1. RAG search
        results = collection.query(
            query_texts=[topic],
            n_results=chunks_per_question + 2,
            include=["documents", "distances"],
        )

        # Filtrujemy tylko dobre chunki
        good_chunks = []
        for doc, dist in zip(results["documents"][0], results["distances"][0]):
            if dist < max_distance:
                good_chunks.append(doc)

        context = "\n\n".join(good_chunks[:chunks_per_question])
        has_good_context = len(good_chunks) > 0

        no_context_note = (
            (
                "Uwaga: nie znaleziono wystarczająco bliskich fragmentów w dokumencie "
                "(distance >= 0.5). Możesz bazować na ogólnej wiedzy eksperckiej, "
                "ale distraktory muszą być bardzo wiarygodne."
            )
            if not has_good_context
            else ""
        )

        # 2. Budujemy prompt
        prompt = QUIZ_USER_PROMPT_TEMPLATE.format(
            topic=topic,
            context=context or "BRAK ODPOWIEDNIEGO FRAGMENTU",
            no_context_note=no_context_note,
        )

        # 3. Wywołanie modelu
        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=800,
        )

        raw = response.choices[0].message.content.strip()

        # Czyszczenie ewentualnego markdown
        if raw.startswith("```"):
            raw = "\n".join(
                line for line in raw.split("\n") if not line.startswith("```")
            )

        try:
            data = json.loads(raw)

            # Dodajemy metadane przydatne dla frontend/backend
            data["topic"] = topic
            data["used_chunks_count"] = len(good_chunks)
            data["max_distance_used"] = max_distance

            # Mieszamy opcje losowo (żeby poprawna nie była zawsze na tej samej pozycji)
            options = data["options"]
            correct_answer = options[data["correct_index"]]
            random.shuffle(options)
            new_correct_index = options.index(correct_answer)

            data["options"] = options
            data["correct_index"] = new_correct_index

            quiz.append(data)

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(
                "Nie udało się sparsować pytania dla tematu '%s': %s", topic, e
            )
            continue

    return quiz
