from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def tg_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    button_1 = KeyboardButton("/Новый_вопрос")
    button_2 = KeyboardButton("/Сдаться")
    button_3 = KeyboardButton("/Мой_счет")
    keyboard.add(button_1, button_2, button_3)
    return keyboard


def is_new_question_command(message):
    return message.text == "/Новый_вопрос"


def is_give_up_command(message):
    return message.text == "/Сдаться"


def is_my_score_command(message):
    return message.text == "/Мой_счет"


def vk_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый_вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button('Мой_счет', color=VkKeyboardColor.POSITIVE)
    return keyboard
