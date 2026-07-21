import os

from langchain_openrouter import ChatOpenRouter
from pydantic import BaseModel

from app.domain.models import AppSettings, Question, WordFeedback


class _WordCheckResponse(BaseModel):
    feedback: list[WordFeedback]


class AIService:
    def __init__(self, settings: AppSettings) -> None:
        if not settings.openrouter_api_key:
            raise ValueError("OpenRouter API key is not set. Add it in Settings.")
        os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key
        self._model = ChatOpenRouter(model=settings.ai_model, temperature=0)

    def check_words(self, words: list[str], context: str) -> list[WordFeedback]:
        checker = self._model.with_structured_output(_WordCheckResponse)
        response = checker.invoke(
            [
                (
                    "system",
                    "You are an English spelling and grammar checker. For each "
                    "word provided, identify any spelling or grammar problem in "
                    "how it was used and give a short suggestion to fix it. "
                    "Only include words that have problems.",
                ),
                (
                    "user",
                    f"Context passage:\n{context}\n\n"
                    f"Words to check: {', '.join(words)}",
                ),
            ]
        )
        return response.feedback

    def generate_question(self, passage_text: str) -> Question:
        generator = self._model.with_structured_output(Question)
        return generator.invoke(
            [
                (
                    "system",
                    "You create reading-comprehension questions for English "
                    "learners. Create exactly one question about the passage, "
                    "choosing one kind:\n"
                    "- mcq: 4 options, answer is the correct option text\n"
                    "- matching: options are 'left|right' pairs to match\n"
                    "- simple: a short-answer question, answer is the expected "
                    "answer\n"
                    "- fill_blank: prompt contains '____', answer is the "
                    "missing word or phrase",
                ),
                ("user", passage_text),
            ]
        )
