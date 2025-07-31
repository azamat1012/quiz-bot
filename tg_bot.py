import argparse
import os
import json
import logging
import random

from dotenv import load_dotenv
import redis
from telebot import TeleBot

from keyboards import (
    tg_keyboard, is_new_question_command,
    is_score_command, is_give_up_command
)
from utils import parse_quiz_file

logger = logging.getLogger(__name__)


def handle_start_command(bot, redis_db, message):
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


def handle_new_question_command(bot, redis_db, questions_dictionary, message):
    try:
        questions_limit = len(questions_dictionary)
        random_question = questions_dictionary[random.randint(
            0, questions_limit)]

        tg_id = str(message.chat.id)
        username = message.from_user.username
        logger.info(f"User: {username} pressed: ASK QUESTION button")

        previous_question_json = redis_db.get(tg_id)
        if previous_question_json:
            previous_question = json.loads(previous_question_json)

        redis_db.set(tg_id, json.dumps(random_question))

        response = "🧐Новый вопрос:\n"
        response += f"{random_question['Вопрос']}\n\n"
        response += "Пожалуйста, напиши свой ответ:"

        bot.send_message(tg_id, response)
    except Exception:
        logging.exception()


def handle_user_answer(bot, redis_db, message):
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
    except Exception:
        logging.exception()


def handle_give_up_command(bot, redis_db, questions_dictionary, message):
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

        bot.send_message(tg_id, f"✅ Правильный ответ был: {correct_answer}")

        # Новый вопрос
        questions_limit = len(questions_dictionary)
        random_question = questions_dictionary[random.randint(
            0, questions_limit)]

        redis_db.set(tg_id, json.dumps(random_question))

        response = "🧐Новый вопрос:\n"
        response += f"{random_question['Вопрос']}\n\n"
        response += "Пожалуйста, напиши свой ответ:"

        bot.send_message(tg_id, response, reply_markup=tg_keyboard())
    except Exception:
        logging.exception()


def handle_score_command(bot, redis_db, message):
    try:
        tg_id = str(message.chat.id)
        username = message.from_user.username
        score = redis_db.get(f"score:{tg_id}") or 0
        bot.send_message(
            tg_id, f"{username}, твой счёт: {score} правильных ответов!")
    except Exception:
        logging.exception()


def handle_start_message(bot, redis_db, message):
    return handle_start_command(bot, redis_db, message)


def handle_new_question_message(bot, redis_db, questions_dictionary, message):
    return handle_new_question_command(bot, redis_db, questions_dictionary, message)


def handle_user_answer_message(bot, redis_db, message):
    return handle_user_answer(bot, redis_db, message)


def handle_give_up_message(bot, redis_db, questions_dictionary, message):
    return handle_give_up_command(bot, redis_db, questions_dictionary, message)


def handle_my_score_message(bot, redis_db, message):
    return handle_score_command(bot, redis_db, message)


def setup_bot_handlers(bot, redis_db, questions_dictionary):
    bot.message_handler(commands=['start'])(
        lambda message: handle_start_message(bot, redis_db, message))
    bot.message_handler(func=is_new_question_command)(
        lambda message: handle_new_question_message(bot, redis_db, questions_dictionary, message))
    bot.message_handler(func=lambda message: not message.text.startswith(
        '/'))(lambda message: handle_user_answer_message(bot, redis_db, message))
    bot.message_handler(func=is_give_up_command)(
        lambda message: handle_give_up_message(bot, redis_db, questions_dictionary, message))
    bot.message_handler(func=is_score_command)(
        lambda message: handle_my_score_message(bot, redis_db, message))


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger.info("Бот запущен")

    load_dotenv()

    telegram_bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    bot = TeleBot(telegram_bot_token)
    redis_db = redis.Redis(
        host=os.environ["REDIS_HOST"],
        port=os.environ["REDIS_PORT"],
        decode_responses=True,
        username="default",
        password=os.environ["REDIS_PASSWORD"],
    )

    parser = argparse.ArgumentParser(description="Парсит файл для квиза")
    parser.add_argument(
        "--file", help="Название файла для парсинга", default="")
    args = parser.parse_args()

    file_path = args.file
    questions_dictionary = parse_quiz_file(
        file_path) if file_path else parse_quiz_file("1vs1200.txt")

    setup_bot_handlers(bot, redis_db, questions_dictionary)
    bot.polling()


if __name__ == "__main__":
    main()
