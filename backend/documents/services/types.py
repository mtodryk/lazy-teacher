from dataclasses import dataclass, field


@dataclass
class QuestionOption:
    text: str


@dataclass
class QuestionData:
    question: str
    options: list[str]
    correct_index: int  # Index of the correct answer (0-3)
    topic: str = ""
    used_chunks_count: int = 0
    max_distance_used: float = 0.0


@dataclass
class QuizData:
    questions: list[QuestionData] = field(default_factory=list)

    def add_question(self, question: QuestionData) -> None:
        self.questions.append(question)

    def count(self) -> int:
        return len(self.questions)

    def to_dict(self) -> list[dict]:
        return [
            {
                "question": q.question,
                "options": q.options,
                "correct_index": q.correct_index,
                "topic": q.topic,
                "used_chunks_count": q.used_chunks_count,
                "max_distance_used": q.max_distance_used,
            }
            for q in self.questions
        ]


@dataclass
class RetrievalContext:
    documents: list[str]
    distances: list[float]

    def get_good_chunks(self, max_distance: float) -> list[str]:
        return [
            doc
            for doc, dist in zip(self.documents, self.distances)
            if dist < max_distance
        ]

    def has_good_context(self, max_distance: float) -> bool:
        return len(self.get_good_chunks(max_distance)) > 0


@dataclass
class LlmResponse:
    content: str

    def extract_json(self) -> str:
        raw = self.content.strip()
        if raw.startswith("```"):
            raw = "\n".join(
                line for line in raw.split("\n") if not line.startswith("```")
            )
        return raw
