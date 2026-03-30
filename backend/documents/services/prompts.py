TOPIC_EXTRACTION_SYSTEM = (
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

TOPIC_EXTRACTION_USER = (
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


QUIZ_GENERATION_SYSTEM = (
    "Jesteś ekspertem od tworzenia bardzo wysokiej jakości pytań testowych na poziomie eksperckim (C1/C2).\n"
    "Pytania muszą być oparte wyłącznie na podanym kontekście z dokumentu.\n"
    "Zasady ściśle:\n"
    "- Dokładnie 1 poprawna odpowiedź\n"
    "- 3 wiarygodne, ale błędne distraktory (nie oczywiste, nie głupie)\n"
    "- Pytanie po polsku, profesjonalne, precyzyjne\n"
    "- Bez 'żaden z powyższych', 'wszystkie powyższe', 'nie wiem' itp.\n"
    "- Zwróć TYLKO czysty JSON, nic więcej."
)

QUIZ_GENERATION_USER = (
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
    '  "options": ["opcja1", "opcja2", "opcja3", "opcja4"],\n'
    '  "correct_index": 0\n'
    "}}\n"
    "correct_index = numer poprawnej opcji (0-3)"
)

NO_CONTEXT_WARNING = (
    "Uwaga: nie znaleziono wystarczająco bliskich fragmentów w dokumencie "
    "(distance >= {max_distance}). Możesz bazować na ogólnej wiedzy eksperckiej, "
    "ale distraktory muszą być bardzo wiarygodne."
)

EXPLANATION_SYSTEM = (
    "Jesteś ekspertem-nauczycielem, który pomaga studentom zrozumieć materiał.\n"
    "Twoim zadaniem jest wyjaśnić, dlaczego dany odpowiedz na pytanie jest poprawny, "
    "opierając się WYŁĄCZNIE na podanym kontekście z dokumentu.\n"
    "Zasady:\n"
    "- Odpowiadaj po polsku, profesjonalnie i przystępnie.\n"
    "- Wyjaśniaj zwięźle, ale treściwie (3-6 zdań).\n"
    "- Odwołuj się konkretnie do fragmentów z kontekstu.\n"
    "- Jeśli kontekst jest niewystarczający, powiedz o tym wprost.\n"
    "- Nie wymyślaj informacji, których nie ma w kontekście."
)

EXPLANATION_USER = (
    'Pytanie: "{question}"\n'
    'Poprawna odpowiedź: "{correct_answer}"\n\n'
    "Kontekst z dokumentu:\n"
    "<context>\n"
    "{context}\n"
    "</context>\n\n"
    "Wyjaśnij, dlaczego ta odpowiedź jest poprawna, opierając się na powyższym kontekście."
)

FOLLOWUP_SYSTEM = (
    "Jesteś ekspertem-nauczycielem, który pomaga studentom zrozumieć materiał.\n"
    "Kontynuujesz rozmowę na temat konkretnego pytania z quizu.\n"
    "Odpowiadaj po polsku, zwięźle i przystępnie.\n"
    "Opieraj się na kontekście z dokumentu podanym wcześniej.\n"
    "Nie wymyślaj informacji, których nie było w kontekście."
)
