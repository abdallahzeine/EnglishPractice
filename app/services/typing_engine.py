from app.domain.models import TypedWord, TypingMetrics


def diff_words(original: str, typed: str) -> list[TypedWord]:
    original_words = original.split()
    typed_words = typed.split()
    result: list[TypedWord] = []
    for index, word in enumerate(original_words):
        if index < len(typed_words):
            status = "correct" if typed_words[index] == word else "incorrect"
        else:
            status = "pending"
        result.append(TypedWord(word=word, status=status))
    return result


def is_finished(original: str, typed: str) -> bool:
    return len(typed.split()) >= len(original.split())


def compute_metrics(original: str, typed: str, elapsed_seconds: float) -> TypingMetrics:
    words = diff_words(original, typed)
    correct = sum(1 for w in words if w.status == "correct")
    total = len(words)
    accuracy = (correct / total * 100) if total else 0.0
    minutes = max(elapsed_seconds, 1.0) / 60
    wpm = (len(typed) / 5) / minutes
    return TypingMetrics(
        wpm=round(wpm, 1),
        accuracy=round(accuracy, 1),
        elapsed_seconds=round(elapsed_seconds, 1),
    )
