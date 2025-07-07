from utils import parse_quiz_file
import os
import json
import logging
import random

from dotenv import load_dotenv
import redis
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from keyboards import (
    tg_keyboard, is_new_question_command,
    is_my_score_command, is_give_up_command
)

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger.info("Бот запущен")

    load_dotenv()
    TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
    bot = TeleBot(TELEGRAM_BOT_TOKEN)
    file_name = "1vs1200.txt"  # Файл с вопросами

    redis_db = redis.Redis(
        host=os.environ.get("REDIS_HOST"),
        port=os.environ.get("REDIS_PORT"),
        decode_responses=True,
        username="default",
        password=os.environ.get("REDIS_PASSWORD"),
    )

    @bot.message_handler(commands=['start'])
    def start(message):
        try:
            tg_id = str(message.chat.id)
            username = message.from_user.username
            logger.info(f"Новый юзер: {username}\nTG: {tg_id}")
            if not redis_db.exists(f"score:{tg_id}"):
                redis_db.set(f"score:{tg_id}", 0)
            bot.send_message(
                tg_id,
                f"🥳🥳🥳\nПриветствуем тебя, {username}, в нашей викторине!\n"
                "Нажми на кнопку 'Новый вопрос'",
                reply_markup=tg_keyboard()
            )
        except Exception as e:
            logger.error(e)

    @bot.message_handler(func=is_new_question_command)
    def handle_new_question_command(message):
        questions_dictionary = parse_quiz_file(file_name)
        questions_limit = len(questions_dictionary)
        random_question = questions_dictionary[random.randint(
            0, questions_limit)]

        try:
            tg_id = str(message.chat.id)
            username = message.from_user.username
            logger.info(f"User: {username} pressed: ASK QUESTION button")

            previous_question = None
            previous_question_json = redis_db.get(tg_id)
            if previous_question_json:
                previous_question = json.loads(previous_question_json)

            redis_db.set(tg_id, json.dumps(random_question))

            response = "🧐Новый вопрос:\n"
            response += f"{random_question['Вопрос']}\n\n"
            response += "Пожалуйста, напиши свой ответ:"

            bot.send_message(tg_id, response)
        except Exception as e:
            logger.error(e)

    @bot.message_handler(func=lambda message: not message.text.startswith('/'))
    def handle_user_answer(message):
        try:
            tg_id = str(message.chat.id)
            user_answer = message.text.strip()

            current_question_json = redis_db.get(tg_id)
            if not current_question_json:
                bot.send_message(tg_id, "Сначала запроси новый вопрос!")
                return

            current_question = json.loads(current_question_json)
            correct_answer = current_question["Ответ"].strip().lower()

            if user_answer.lower() == correct_answer:
                response = "✅ Правильно!\n"
                redis_db.incr(f"score:{tg_id}")
            else:
                response = f"❌ Не-а"

            response += "\nНажми 'Новый вопрос' для продолжения!"
            bot.send_message(tg_id, response, reply_markup=tg_keyboard())
        except Exception as e:
            logger.error(e)

    @bot.message_handler(func=is_give_up_command)
    def handle_give_up_command(message):
        try:
            tg_id = str(message.chat.id)
            username = message.from_user.username
            logger.info(f"Юзер: {username} нажал на кнопку: сдаться")

            current_question_json = redis_db.get(tg_id)
            if not current_question_json:
                bot.send_message(tg_id, "Пожалуйста, запросите вопрос")
                return

            current_question = json.loads(current_question_json)
            correct_answer = current_question["Ответ"].strip()

            bot.send_message(
                tg_id, f"✅ Правильный ответ был: {correct_answer}")

            # Новый вопрос
            questions_dictionary = parse_quiz_file(file_name)
            questions_limit = len(questions_dictionary)
            random_question = questions_dictionary[random.randint(
                0, questions_limit)]

            redis_db.set(tg_id, json.dumps(random_question))

            response = "🧐Новый вопрос:\n"
            response += f"{random_question['Вопрос']}\n\n"
            response += "Пожалуйста, напиши свой ответ:"

            bot.send_message(tg_id, response, reply_markup=tg_keyboard())
        except Exception as e:
            logger.error(e)

    @bot.message_handler(func=is_my_score_command)
    def handle_my_score_command(message):
        try:
            tg_id = str(message.chat.id)
            username = message.from_user.username
            score = redis_db.get(f"score:{tg_id}") or 0
            bot.send_message(
                tg_id, f"{username}, твой счёт: {score} правильных ответов!")
        except Exception as e:
            logger.error(e)

    bot.polling()


if __name__ == "__main__":
    main()
