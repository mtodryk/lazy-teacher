# 🚀 Lazy Teacher

[Polish version](README_PL.md)

## Live Links

* **Demo:** https://lazy-teacher.hackvisa.online (temporarily unavailable)
* **API Documentation (Swagger):** https://lazy-teacher.hackvisa.online/api/docs/ (temporarily unavailable)

## 📚 About the Project

**Lazy Teacher** is an AI-powered educational platform designed to automate and support the learning and teaching process.

The system consists of a modern frontend application, a backend based on a microservices architecture with asynchronous task processing, and an integrated vector database for advanced text and document processing.

## 🎯 Project Goal and Target Audience

Lazy Teacher is designed for people involved in education, including:

* **Teachers and lecturers** — generate quizzes and assessment materials based on educational content.
* **Tutors** — quickly create customized exercises based on specific documents, such as student notes or textbook excerpts.
* **Students** — test their knowledge using automatically generated quizzes and flashcards based on lecture notes or books.

### Problem Solved

Creating personalized and reliable tests based on specific source material, such as PDF notes, can be time-consuming. Lazy Teacher automates this process using **Large Language Models (LLMs)** and **Retrieval-Augmented Generation (RAG)**.

## ⚙️ How It Works

The platform uses an intelligent data processing pipeline:

1. **Upload materials** — the user uploads a document, such as a PDF, through the web interface.
2. **Asynchronous processing** — document processing tasks are added to a **Celery/Redis** queue, allowing users to continue using the application without waiting.
3. **Text extraction and splitting** — PDF content is extracted using `pymupdf4llm` and divided into logical chunks using `langchain-text-splitters`.
4. **Embeddings** — each text chunk is converted into a vector representation using `sentence-transformers` and PyTorch.
5. **Indexing and search** — embeddings are stored in **ChromaDB**, enabling semantic search across the uploaded documents.
6. **Quiz generation** — when a user requests a quiz, the system sends the most relevant document fragments to the **OpenAI API**, which generates questions, answers, and distractors.
7. **Result presentation** — the Django backend stores generated quizzes in **PostgreSQL** and sends them to the **Next.js** frontend, where users can solve, edit, or share them.

## 🐳 System Architecture and Services

The application is fully containerized and uses **Docker Compose** to orchestrate the following services:

* **PostgreSQL** — stores users, quiz metadata, documents, and other application data.
* **Redis** — message broker for asynchronous Celery tasks and application caching.
* **ChromaDB** — vector database storing document embeddings for semantic search.
* **Django backend** — main Python backend providing the application API.
* **Celery worker** — handles resource-intensive background processing tasks.

## 🛠️ Technology Stack

### Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS
* ESLint

### Backend

* Python
* Django
* Django REST Framework
* PostgreSQL
* Celery
* Redis
* drf-spectacular
* AWS S3

### AI & Machine Learning

* OpenAI API
* Retrieval-Augmented Generation (RAG)
* ChromaDB
* PyTorch
* sentence-transformers
* LangChain text splitters
* PyMuPDF4LLM

### Infrastructure

* Docker
* Docker Compose
* AWS S3

## 🧪 Testing

Backend functionality is tested using **pytest**.

Tests cover the main application modules, including:

* Documents
* Quizzes
* Users
<img width="942" height="926" alt="image" src="https://github.com/user-attachments/assets/6d4bdc78-aa49-4edd-b1e8-57defbe7616a" />

The project also includes:

* Integration tests
* Long-running tests
* Code coverage reports
* Custom Django management commands

## 👥 Team

The project was developed as a **3-person team**, with responsibilities divided between AI/database development, backend development, and frontend development.

* **Database / AI Developer** — database system and AI agent integration
* **Backend Developer** — quiz structures, business logic, and API endpoints
* **Frontend Developer** — Next.js configuration, user interface, and client-side authorization

## ✨ Features

* User registration and authentication
* User and administrator accounts
* Document upload and processing
* Automatic quiz generation
* AI-powered explanations
* RAG-based AI chat <img width="1140" height="871" alt="image" src="https://github.com/user-attachments/assets/7a2094d3-e004-4383-bfbf-705c0ab7fbc3" />

* Automatic generation of questions, answers, and distractors
* Quiz editing and solving
* Quiz sharing without requiring authentication
* Responsive UI built with Tailwind CSS
* REST API with Swagger documentation

## 🚀 Development Setup

All services can be started using Docker Compose.

### 1. Clone the repository

```bash
git clone <repository-url>
cd lazy-teacher
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Add the required API keys and configuration values to the `.env` file.

### 3. Start the application

```bash
docker-compose up -d --build
```

### 4. Start the frontend in development mode

```bash
cd frontend
npm install
npm run dev
```
