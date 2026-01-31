"""
Модуль админ-панели для бота ALMARIS.
Упрощённая версия — только управление одной инструкцией.
"""

from aiogram import Router, types, F
from aiogram.filters.command import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

import storage

router = Router()


class AdminStates(StatesGroup):
    """Состояния FSM для админ-панели."""
    waiting_password = State()
    main_menu = State()
    upload_instruction = State()
    edit_instruction_text = State()


def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню админки."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📄 Загрузить инструкцию (файл)")],
            [KeyboardButton(text="✏️ Изменить текст инструкции")],
            [KeyboardButton(text="👁 Посмотреть текущую инструкцию")],
            [KeyboardButton(text="🚪 Выйти из админки")]
        ],
        resize_keyboard=True
    )


# ==================== КОМАНДА /admin ====================

@router.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    """Обработчик команды /admin."""
    if message.chat.type != "private":
        return await message.reply("❌ Команда доступна только в личных сообщениях")
    
    await state.set_state(AdminStates.waiting_password)
    await message.answer(
        "🔐 Введите пароль администратора:",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(AdminStates.waiting_password, F.text)
async def process_password(message: types.Message, state: FSMContext):
    """Проверка пароля."""
    password = message.text
    correct_password = storage.get_admin_password()
    
    if password != correct_password:
        await state.clear()
        return await message.answer("❌ Неверный пароль. Доступ запрещён.")
    
    await state.set_state(AdminStates.main_menu)
    await message.answer(
        "✅ Добро пожаловать в админ-панель!\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu_keyboard()
    )


# ==================== ГЛАВНОЕ МЕНЮ ====================

@router.message(AdminStates.main_menu, F.text == "👁 Посмотреть текущую инструкцию")
async def view_instruction(message: types.Message, state: FSMContext):
    """Показать текущую инструкцию."""
    instruction = storage.get_instruction()
    
    file_id = instruction.get("file_id")
    text = instruction.get("text")
    
    if not file_id and not text:
        return await message.answer("📭 Инструкция пока не загружена")
    
    if file_id:
        await message.answer_document(document=file_id)
    
    if text:
        await message.answer(f"📝 Текст инструкции:\n\n{text}")
    else:
        await message.answer("📝 Текст инструкции не задан")


@router.message(AdminStates.main_menu, F.text == "📄 Загрузить инструкцию (файл)")
async def upload_instruction_start(message: types.Message, state: FSMContext):
    """Начало загрузки инструкции."""
    await state.set_state(AdminStates.upload_instruction)
    await message.answer(
        "📄 Отправьте файл с инструкцией:\n\n"
        "(Или отправьте /cancel для отмены)",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(AdminStates.upload_instruction, Command("cancel"))
async def upload_instruction_cancel(message: types.Message, state: FSMContext):
    """Отмена загрузки инструкции."""
    await state.set_state(AdminStates.main_menu)
    await message.answer("Отменено", reply_markup=get_admin_menu_keyboard())


@router.message(AdminStates.upload_instruction, F.document)
async def upload_instruction_process(message: types.Message, state: FSMContext):
    """Обработка загруженной инструкции."""
    file_id = message.document.file_id
    
    if storage.update_instruction(file_id=file_id):
        await message.answer(
            "✅ Инструкция успешно загружена!",
            reply_markup=get_admin_menu_keyboard()
        )
    else:
        await message.answer("❌ Ошибка при сохранении", reply_markup=get_admin_menu_keyboard())
    
    await state.set_state(AdminStates.main_menu)


@router.message(AdminStates.main_menu, F.text == "✏️ Изменить текст инструкции")
async def edit_instruction_text_start(message: types.Message, state: FSMContext):
    """Начало редактирования текста инструкции."""
    await state.set_state(AdminStates.edit_instruction_text)
    await message.answer(
        "✏️ Введите новый текст для инструкции:\n\n"
        "(Или отправьте /cancel для отмены)",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(AdminStates.edit_instruction_text, Command("cancel"))
async def edit_instruction_text_cancel(message: types.Message, state: FSMContext):
    """Отмена редактирования текста."""
    await state.set_state(AdminStates.main_menu)
    await message.answer("Отменено", reply_markup=get_admin_menu_keyboard())


@router.message(AdminStates.edit_instruction_text, F.text)
async def edit_instruction_text_process(message: types.Message, state: FSMContext):
    """Обработка нового текста инструкции."""
    if storage.update_instruction(text=message.text):
        await message.answer("✅ Текст инструкции обновлён!", reply_markup=get_admin_menu_keyboard())
    else:
        await message.answer("❌ Ошибка при сохранении", reply_markup=get_admin_menu_keyboard())
    
    await state.set_state(AdminStates.main_menu)


@router.message(AdminStates.main_menu, F.text == "🚪 Выйти из админки")
async def exit_admin(message: types.Message, state: FSMContext):
    """Выход из админки."""
    await state.clear()
    await message.answer(
        "👋 Вы вышли из админ-панели.",
        reply_markup=ReplyKeyboardRemove()
    )
