import os
import json
import logging
import random
from time import sleep

import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from dotenv import load_dotenv
import redis

from keyboards import vk_keyboard
from utils import parse_quiz_file

logger = logging.getLogger(__name__)


class VkLogHandler(logging.Handler):
    def __init__(self, vk_api, chat_id):
        super().__init__()
        self.vk_api = vk_api
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        try:
            self.vk_api.messages.send(
                user_id=self.chat_id,
                message=log_entry,
                random_id=random.randint(1, 100000)
            )
        except Exception as e:
            print("Ошибка с отправкой сообщения:", e)


def handle_messages(event, vk_api, redis_db, questions_dictionary):
    user_id = str(event.user_id)
    text = event.text.strip()

    if text == "/start":
        if not redis_db.exists(f"score:{user_id}"):
            redis_db.set(f"score:{user_id}", 0)

        user_info = vk_api.users.get(user_ids=user_id)
        username = user_info[0]['first_name']

        vk_api.messages.send(
            user_id=event.user_id,
            message=f"""🥳🥳🥳\nПриветствуем тебя, {username}, в нашей 
                    викторине!\nНажми на кнопку 'Новый вопрос'""",
            random_id=random.randint(1, 1000),
            keyboard=vk_keyboard().get_keyboard()
        )

    elif text == "Новый_вопрос":
        questions_limit = len(questions_dictionary)
        random_question = questions_dictionary[random.randint(
            0, questions_limit)]
        redis_db.set(user_id, json.dumps(random_question))

        response = "🧐Новый вопрос:\n"
        response += f"{random_question['Вопрос']}\n\n"
        response += "Пожалуйста, напиши свой ответ:"

        vk_api.messages.send(
            user_id=event.user_id,
            message=response,
            random_id=random.randint(1, 1000)
        )

    elif text == "Сдаться":
        current_question_json = redis_db.get(user_id)
        if not current_question_json:
            vk_api.messages.send(
                user_id=event.user_id,
                message="Пожалуйста, запросите вопрос",
                random_id=random.randint(1, 1000),
                keyboard=vk_keyboard().get_keyboard()
            )
            return

        current_question = json.loads(current_question_json)
        correct_answer = current_question["Ответ"].strip()

        questions_limit = len(questions_dictionary)
        random_question = questions_dictionary[random.randint(
            0, questions_limit)]
        redis_db.set(user_id, json.dumps(random_question))

        response = f"✅ Правильный ответ был: {correct_answer}\n\n"
        response += "🧐Новый вопрос:\n"
        response += f"{random_question['Вопрос']}\n\n"
        response += "Пожалуйста, напиши свой ответ:"

        vk_api.messages.send(
            user_id=event.user_id,
            message=response,
            random_id=random.randint(1, 1000),
            keyboard=vk_keyboard().get_keyboard()
        )

    elif text == "Мой_счет":
        user_info = vk_api.users.get(user_ids=user_id)
        username = user_info[0]['first_name'] if user_info else 'Пользователь'
        score = redis_db.get(f"score:{user_id}") or 0

        vk_api.messages.send(
            user_id=event.user_id,
            message=f"{username}, твой счёт: {score} правильных ответов!",
            random_id=random.randint(1, 1000),
            keyboard=vk_keyboard().get_keyboard()
        )

    else:
        current_question_json = redis_db.get(user_id)
        current_question = json.loads(current_question_json)
        correct_answer = current_question["Ответ"].strip().lower()

        if text.lower() == correct_answer:
            response = "✅ Правильно!\n"
            redis_db.incr(f"score:{user_id}")
        else:
            response = "❌ Не-а"

        vk_api.messages.send(
            user_id=event.user_id,
            message=response,
            random_id=random.randint(1, 1000),
            keyboard=vk_keyboard().get_keyboard()
        )


def start_bot(vk_bot_token: str, admin_chat_id):
    redis_db = redis.Redis(
        host=os.environ.get('REDIS_HOST'),
        port=19927,
        decode_responses=True,
        username="default",
        password=os.environ.get('REDIS_PASSWORD'),
    )
    file_name = "1vs1200.txt"
    questions_dictionary = parse_quiz_file(file_name)

    vk_session = vk.VkApi(token=vk_bot_token)
    vk_api = vk_session.get_api()
    logger.info(f"Бот активирован с токеном: {vk_bot_token[:5]}...")

    if admin_chat_id:
        vk_handler = VkLogHandler(vk_api, admin_chat_id)
        vk_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        vk_handler.setFormatter(formatter)
        logger.addHandler(vk_handler)
        logger.info(f"Логи будут отправляться в VK чат: {admin_chat_id}")
    else:
        logger.info("ADMIN_CHAT_ID не указан, логи будут только в консоли")

    long_poll = VkLongPoll(vk_session)
    logger.info("Начинаю слушать события...")

    for event in long_poll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            logger.info(f"Получен запрос от {event.user_id}: '{event.text}'")
            try:
                handle_messages(event, vk_api, redis_db, questions_dictionary)
            except Exception as e:
                logger.error(f"Ошибка при обработке сообщения: {str(e)}")


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    load_dotenv()

    vk_bot_token = os.environ.get('VK_BOT_TOKEN')
    admin_chat_id = os.environ.get('ADMIN_CHAT_ID_VK') or None

    if not vk_bot_token:
        logger.error(
            "VK_BOT_TOKEN не найден. Пожалуйста, добавьте VK_BOT_TOKEN в .env"
        )
        return

    while True:
        try:
            start_bot(vk_bot_token, admin_chat_id)
        except Exception as e:
            logger.error(f"Произошла ошибка: {e}")
            sleep(5)
            continue


if __name__ == "__main__":
    main()
