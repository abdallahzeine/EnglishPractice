from app.services.typing_engine import compute_metrics, diff_words, is_finished


def test_diff_marks_correct_incorrect_pending() -> None:
    words = diff_words("the cat sat", "the dog")
    assert [w.status for w in words] == ["correct", "incorrect", "pending"]


def test_finished_when_all_words_typed() -> None:
    assert is_finished("one two", "one two")
    assert is_finished("one two", "one two extra")
    assert not is_finished("one two", "one")


def test_metrics_accuracy_and_speed() -> None:
    metrics = compute_metrics("the cat sat", "the dog sat", 60.0)
    assert metrics.accuracy == round(2 / 3 * 100, 1)
    assert metrics.wpm > 0
    assert metrics.elapsed_seconds == 60.0


if __name__ == "__main__":
    test_diff_marks_correct_incorrect_pending()
    test_finished_when_all_words_typed()
    test_metrics_accuracy_and_speed()
    print("typing engine tests ok")
