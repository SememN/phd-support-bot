"""
Модуль для работы с хранилищем данных (data.json).
Упрощённая версия — только одна инструкция для одного товара.
"""

import json
import os
from typing import Optional

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')

# Структура по умолчанию
DEFAULT_DATA = {
    "bot_token": "",
    "support_chat": 0,
    "admin_password": "almaris2024",
    "thanks_message": "Благодарим вас за покупку! С уважением, команда бренда ALMARIS❤️",
    "instruction": {
        "file_id": None,
        "text": None
    }
}


def load_data() -> dict:
    """Загружает данные из JSON-файла."""
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return DEFAULT_DATA.copy()


def save_data(data: dict) -> bool:
    """Сохраняет данные в JSON-файл."""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False


def get_bot_token() -> str:
    """Возвращает токен бота."""
    data = load_data()
    return data.get("bot_token", "")


def get_support_chat() -> int:
    """Возвращает ID чата поддержки."""
    data = load_data()
    return data.get("support_chat", 0)


def set_support_chat(chat_id: int) -> bool:
    """Устанавливает ID чата поддержки."""
    data = load_data()
    data["support_chat"] = chat_id
    return save_data(data)


def get_admin_password() -> str:
    """Возвращает пароль администратора."""
    data = load_data()
    return data.get("admin_password", "almaris2024")


def get_thanks_message() -> str:
    """Возвращает сообщение благодарности."""
    data = load_data()
    return data.get("thanks_message", "Спасибо за покупку!")


def get_instruction() -> dict:
    """Возвращает данные инструкции (file_id и text)."""
    data = load_data()
    return data.get("instruction", {"file_id": None, "text": None})


def update_instruction(file_id: Optional[str] = None, text: Optional[str] = None) -> bool:
    """Обновляет инструкцию (файл и/или текст)."""
    data = load_data()
    
    if "instruction" not in data:
        data["instruction"] = {"file_id": None, "text": None}
    
    if file_id is not None:
        data["instruction"]["file_id"] = file_id
    
    if text is not None:
        data["instruction"]["text"] = text
    
    return save_data(data)
