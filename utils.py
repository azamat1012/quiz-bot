import os
from typing import Dict


def parse_quiz_file(file_path: str) -> Dict[int, Dict[str, str]]:
    """Сортирует файл с вопросами и возваращает актуальный вопрос с ответом"""
    current_directory = os.path.dirname(os.path.abspath(__file__))

    if file_path:
        with open(f"{current_directory}/quiz-questions/{file_path}", "r", encoding="utf") as quiz_file:
            content_of_quiz_file = quiz_file.read()
    else:
        with open(f"{current_directory}/quiz-questions/1vs1200.txt", "r", encoding="utf") as quiz_file:
            content_of_quiz_file = quiz_file.read()

    questions = {}
    current_question = None
    question_number = 1
    sections = content_of_quiz_file.split("\n\n")

    for section in sections:
        edited_section = section.strip()
        if edited_section.startswith("Вопрос"):
            current_question = edited_section.partition(":")[2].strip()
            questions[question_number] = {
                "Вопрос": current_question, "Номер": question_number}
        elif edited_section.startswith("Ответ") and current_question:
            questions[question_number]["Ответ"] = edited_section.partition(":")[
                2].strip()
            current_question = None
            question_number += 1
    return questions
