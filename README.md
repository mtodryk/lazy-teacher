Lazy Teacher

Platforma edukacyjna oparta na sztucznej inteligencji, stworzona w celu automatyzacji i wspomagania procesu nauczania. System składa się z nowoczesnej aplikacji frontendowej, wydajnego backendu opartego na architekturze mikroserwisów z systemem kolejkowania zadań oraz zintegrowanej bazy wektorowej do zaawansowanego przetwarzania tekstu i dokumentów.

Cel Projektu i Grupa Docelowa

Do kogo skierowana jest aplikacja?
Aplikacja "Lazy Teacher" została zaprojektowana z myślą o osobach zaangażowanych w proces edukacyjny, w tym:
* Nauczycielach i Wykładowcach: Zmagających się z brakiem czasu na przygotowywanie materiałów dydaktycznych, testów i sprawdzianów. Platforma pozwala im wygenerować gotowe narzędzia weryfikacji wiedzy w kilka sekund.
* Korepetytorach: Poszukujących sposobu na szybkie dostosowanie materiałów ćwiczeniowych do konkretnych dokumentów (np. notatek ucznia, fragmentów podręcznika).
* Uczniach i Studentach : Chcących samodzielnie sprawdzić swoją wiedzę z dostarczonych notatek z wykładów lub książek przed egzaminem, poprzez automatycznie generowane quizy i fiszki.

Rozwiązywany problem :
Tworzenie spersonalizowanych, rzetelnych testów wiedzy na podstawie konkretnego materiału źródłowego (np. pliku PDF z notatkami) jest procesem żmudnym i czasochłonnym. "Lazy Teacher" zdejmuje ten obowiązek z użytkownika, automatyzując cały proces przy użyciu zaawansowanych modeli językowych (LLM) i technik Retrieval-Augmented Generation (RAG).

Jak konkretnie działa aplikacja?

Proces działania platformy opiera się na inteligentnym potoku przetwarzania danych (data pipeline):

1. Wgrywanie materiałów: Użytkownik przesyła dokument (np. plik PDF) poprzez interfejs w przeglądarce.
2. Przetwarzanie w tle (Asynchroniczność): Ze względu na to, że analiza długich dokumentów jest zasobochłonna, zadanie to trafia do kolejki w systemie Celery i Redis. Użytkownik nie musi czekać z zablokowanym ekranem.
3. Ekstrakcja i podział tekstu: Dokument PDF jest czytany i zamieniany na tekst przy użyciu `pymupdf4llm`, a następnie dzielony na mniejsze, logiczne fragmenty (tzw. chunks) z pomocą narzędzi `langchain-text-splitters`.
4. Wektoryzacja (Embeddings): Każdy fragment tekstu jest przekształcany na reprezentację matematyczną (wektor) za pomocą modeli z biblioteki `sentence-transformers` (działającej na PyTorch).
5. Indeksowanie i Wyszukiwanie: Wektory trafiają do wektorowej bazy danych ChromaDB. Dzięki temu system "rozumie" kontekst dokumentu i może błyskawicznie odnajdywać fragmenty powiązane z danym tematem.
6. Generowanie Quizu (LLM): Gdy użytkownik prosi o wygenerowanie testu, system korzysta z API OpenAI, dostarczając modelowi językowemu najbardziej relewantne fragmenty dokumentu. Model na ich podstawie układa trafne pytania, odpowiedzi i dystraktory (błędne odpowiedzi).
7. Prezentacja wyników: Backend (Django) zapisuje wygenerowany quiz w relacyjnej bazie PostgreSQL i przesyła go do Frontendu (Next.js), gdzie użytkownik może go rozwiązać, edytować lub udostępnić.

Architektura Systemu i Usługi (Docker)

Aplikacja jest w pełni konteneryzowana i wykorzystuje `docker-compose` do orkiestracji następujących usług:

* db: Baza danych PostgreSQL (`16-alpine`), z trwałym wolumenem `postgres_data`, odpowiedzialna za przechowywanie danych użytkowników, metadanych quizów i dokumentów. Działa na porcie `5432`.
* redis: Serwer Redis (`7-alpine`) mapowany na port `6379`. Pełni krytyczną funkcję brokera wiadomości dla zadań asynchronicznych (Celery) oraz systemu cache.
* chroma: Baza wektorowa ChromaDB (port `8001`) przechowująca osadzenia (embeddings) dokumentów, z wyłączoną telemetrią. Pozwala na semantyczne przeszukiwanie bazy wiedzy.
* backend: Główna aplikacja serwerowa w języku Python (Django) działająca na porcie `8000`. Posiada limit pamięci RAM ustawiony na 1G.
* celery: Asynchroniczny worker do obsługi obciążających zadań w tle (model `prefork`, max. 50 zadań na proces). Korzysta z wolumenu `hf_cache` dla optymalizacji modeli HuggingFace. Posiada limit pamięci RAM ustawiony na 3G.

Stos Technologiczny

Frontend
* Środowisko i Framework: Next.js 16.1.7
* Biblioteka UI: React 19.2.3 oraz React DOM 19.2.3
* Język: TypeScript 5
* Stylizacja: Tailwind CSS 4.2.1 wraz z PostCSS 8.5.8 i Autoprefixerem
* Narzędzia developerskie: ESLint 9 (lintowanie), zdefiniowane skrypty budowania (`dev`, `build`, `start`)

Backend
* Core: Framework Django 6.0.3 oraz Django REST Framework (>=3.15) do tworzenia API.
* Baza danych: Adapter `psycopg2-binary` (>=2.9).
* Kolejkowanie: Celery (>=5.3) z integracją Redis (>=5.0).
* Dokumentacja API: Automatyczne generowanie schematów przez `drf-spectacular` (>=0.27).
* Zarządzanie Plikami: Integracja z chmurą AWS S3 poprzez `boto3` (>=1.35).
* Bezpieczeństwo: Pakiety takie jak `django-cors-headers`.

AI i Machine Learning
* Integracja LLM: Pakiet `openai` (>=1.0) oraz `langchain-text-splitters`.
* Modele lokalne (CPU): PyTorch 2.9.1 współpracujący z `sentence-transformers` i `einops` do generowania embeddings tekstowych.
* Baza wektorowa: Klient `chromadb` (>=0.5.0).
* Parsowanie PDF: `pymupdf4llm`.


Konfiguracja Testów
Jakość kodu backendowego jest weryfikowana za pomocą `pytest` z konfiguracją opisaną w pliku `pyproject.toml` (ustawienia środowiska: `settings.test_settings`).
* Zakres testów: Aplikacja testuje moduły `documents/tests`, `quizes/tests` oraz `users/tests`.
* Raportowanie (Coverage): Generowane są szczegółowe raporty pokrycia kodu w terminalu (`term-missing`) i jako interaktywne pliki `htmlcov`. Pliki migracyjne, ustawienia i kod testowy są z raportów wykluczane.
* Typy testów: Używane są markery dla testów integracyjnych (`integration`) oraz testów długotrwałych (`slow`).



Podział Zadań w Zespole

Poniżej znajduje się przypisanie odpowiedzialności za poszczególne moduły systemu w naszym zespole:

| Maksym Todryk | Data base/AI Developer |  | 
| Tomasz Bieńkowski | Backend Developer |  | 
| Bartosz Wdowiak | Frontend Developer | Konfiguracja Next.js, interfejs wgrywania plików, rozwiązywania quizów, autoryzacja po stronie klienta. | 



 Uruchomienie Projektu (Development)

Wszystkie usługi można uruchomić za pomocą jednego polecenia dzięki Docker Compose:

```bash
Sklonuj repozytorium

git clone <url-repozytorium>
cd lazy-teacher

Skopiuj pliki konfiguracyjne środowiska (upewnij się, że wpiszesz swoje klucze API)

cp .env.example .env

 Uruchom wszystkie usługi w tle

docker-compose up -d --build

Uruchomienie frontend

cd frontend
npm install
npm run dev
