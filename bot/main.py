"""
Бот поддержки
Упрощённая версия — одна инструкция для одного товара
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters.command import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import storage
import admin

# Загружаем токен из data.json
TOKEN = storage.get_bot_token()

if not TOKEN:
    raise ValueError("Bot token not found in data.json! Please add 'bot_token' field.")

start_message = """Добро пожаловать! Выберите нужный раздел:"""
support_message = """Опишите ваш вопрос, и наши специалисты свяжутся с вами в ближайшее время!"""

help_msg = "Ваш вопрос передан специалистам! С Вами свяжутся в ближайшее время!"

new_question = """Вопрос от пользователя: {question}
Ник: {username}
id пользователя: {user_id}"""

reply_help = "{message}"


class StatesG(StatesGroup):
    waiting_for_question = State()


logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Создаём пользовательский роутер
user_router = Router()

# ВАЖНО: сначала подключаем роутер админки (приоритет выше)
dp.include_router(admin.router)
# Потом подключаем пользовательский роутер
dp.include_router(user_router)


def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="Служба поддержки"),
    )
    builder.row(types.KeyboardButton(text="Инструкция"))
    return builder.as_markup(resize_keyboard=True)


@user_router.message(Command("start"))
async def command_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(start_message, reply_markup=get_main_keyboard())


@user_router.message(Command("setchat"))
async def cmd_setchat(message: types.Message):
    """
    Команда для установки группы поддержки.
    Использование: /setchat <пароль>
    Работает только в группах.
    """
    # Проверяем, что это группа
    if message.chat.type not in ["group", "supergroup"]:
        return await message.reply("❌ Эта команда работает только в группах")
    
    # Извлекаем пароль из сообщения
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("❌ Укажите пароль: /setchat <пароль>")
    
    password = parts[1].strip()
    correct_password = storage.get_admin_password()
    
    if password != correct_password:
        return await message.reply("❌ Неверный пароль")
    
    # Сохраняем chat_id группы
    chat_id = message.chat.id
    if storage.set_support_chat(chat_id):
        await message.reply(
            f"✅ Группа установлена как чат поддержки!\n\n"
            f"Chat ID: `{chat_id}`\n"
            f"Название: {message.chat.title}",
            parse_mode="Markdown"
        )
    else:
        await message.reply("❌ Ошибка при сохранении")


@user_router.message(F.text == "Служба поддержки")
async def support_handler(message: types.Message, state: FSMContext):
    await state.set_state(StatesG.waiting_for_question)
    await message.answer(support_message, reply_markup=ReplyKeyboardRemove())


@user_router.message(F.text == "Инструкция")
async def instruction_handler(message: types.Message, state: FSMContext):
    """Отправка инструкции пользователю."""
    instruction = storage.get_instruction()
    
    file_id = instruction.get("file_id")
    text = instruction.get("text")
    
    if not file_id and not text:
        return await message.answer("Инструкция пока недоступна", reply_markup=get_main_keyboard())
    
    if file_id:
        await message.answer_document(document=file_id)
    
    if text:
        await message.answer(text=text)
    
    # Отправляем благодарность через 2 минуты
    await asyncio.sleep(60 * 2)
    thanks = storage.get_thanks_message()
    await message.answer(thanks, reply_markup=get_main_keyboard())


@user_router.message(StatesG.waiting_for_question, F.text)
async def handle_support_question(message: types.Message, state: FSMContext):
    await state.clear()
    username = "отсутствует" if not message.from_user.username else "@" + message.from_user.username
    keyboard = None

    if message.from_user.username:
        button = InlineKeyboardButton(text="Перейти в чат", url=f"https://t.me/{message.from_user.username}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])

    msg = new_question.format(
        question=message.text,
        username=username,
        user_id=message.from_user.id
    )

    support_chat = storage.get_support_chat()
    if not support_chat:
        return await message.reply("⚠️ Чат поддержки не настроен. Обратитесь к администратору.")
    
    await bot.send_message(
        chat_id=support_chat,
        text=msg,
        reply_markup=keyboard
    )

    await message.reply(help_msg, reply_markup=get_main_keyboard())


@user_router.message(StatesG.waiting_for_question, F.photo | F.video | F.document | F.audio | F.voice | F.sticker | F.animation)
async def handle_support_media(message: types.Message, state: FSMContext):
    await state.clear()
    username = "отсутствует" if not message.from_user.username else "@" + message.from_user.username
    keyboard = None

    if message.from_user.username:
        button = InlineKeyboardButton(text="Перейти в чат", url=f"https://t.me/{message.from_user.username}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])

    if message.photo:
        media_type = "Фото"
    elif message.video:
        media_type = "Видео"
    elif message.document:
        document_name = message.document.file_name or "Неизвестный файл"
        media_type = f"Документ ({document_name})"
    elif message.audio:
        media_type = "Аудио"
    elif message.voice:
        media_type = "Голосовое сообщение"
    elif message.sticker:
        media_type = "Стикер"
    elif message.animation:
        media_type = "GIF"
    else:
        media_type = "Медиафайл"

    msg = new_question.format(
        question=f"{media_type} (см. вложение)\nДля ответа пользователю ответьте на данное сообщение",
        username=username,
        user_id=message.from_user.id
    )

    support_chat = storage.get_support_chat()
    if not support_chat:
        return await message.reply("⚠️ Чат поддержки не настроен. Обратитесь к администратору.")

    await bot.forward_message(
        chat_id=support_chat,
        from_chat_id=message.from_user.id,
        message_id=message.message_id
    )

    await bot.send_message(
        chat_id=support_chat,
        text=msg,
        reply_markup=keyboard
    )

    await message.reply(help_msg, reply_markup=get_main_keyboard())


async def reply_message(message: types.Message):
    text = message.text
    user_id = int(message.reply_to_message.text.split(":")[-1])

    await bot.send_message(
        chat_id=user_id,
        text=reply_help.format(message=text)
    )

    await message.reply("Ответ выслан пользователю!")


@user_router.message(F.text)
async def help_text(message: types.Message, state: FSMContext):
    """ Обработка ответов из чата поддержки."""
    support_chat = storage.get_support_chat()
    if message.chat.id != support_chat:
        return
    if message.reply_to_message:
        return await reply_message(message=message)


@user_router.message(F.photo | F.video | F.document)
async def help_media(message: types.Message, state: FSMContext):
    """Обработка медиа-ответов из чата поддержки."""
    support_chat = storage.get_support_chat()
    if message.chat.id != support_chat:
        return
    if not message.reply_to_message:
        return

    user_id = int(message.reply_to_message.text.split(":")[-1])

    if message.photo:
        await bot.send_photo(
            chat_id=user_id,
            photo=message.photo[-1].file_id,
            caption=message.caption
        )
    elif message.video:
        await bot.send_video(
            chat_id=user_id,
            video=message.video.file_id,
            caption=message.caption
        )
    elif message.document:
        await bot.send_document(
            chat_id=user_id,
            document=message.document.file_id,
            caption=message.caption
        )

    await message.reply("Медиафайл отправлен пользователю!")


@user_router.message(F.text & ~F.text.startswith("/"))
async def other_text_messages(message: types.Message, state: FSMContext):
    # Проверяем, есть ли активное состояние (админка или другое)
    current_state = await state.get_state()
    if current_state is not None:
        return  # Есть активное состояние — не перехватываем
    
    await message.answer("Пожалуйста, выберите один из пунктов меню:", reply_markup=get_main_keyboard())


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
