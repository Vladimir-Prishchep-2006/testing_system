def is_question_correct(selected: set[int], correct: set[int]) -> bool:
    """Вопрос засчитывается, только если выбраны ровно все верные варианты."""
    return selected == correct


def grade_from_percent(percent: float) -> int:
    """Перевод процента правильных ответов в пятибалльную оценку."""
    if percent >= 90:
        return 5
    if percent >= 75:
        return 4
    if percent >= 50:
        return 3
    return 2