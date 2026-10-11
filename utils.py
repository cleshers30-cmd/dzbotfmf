"""
Вспомогательные функции: форматирование текста, отправка сообщений и т.д.
"""

import asyncio
from aiogram import types
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from config import SUBJECTS, DELETE_DELAY, ADMIN_IDS

async def delete_message_later(bot, chat_id: int, message_id: int, delay: int = DELETE_DELAY):
    """Фоновая задача: удаляет сообщение через N секунд."""
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass

def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """Создаёт главную клавиатуру с кнопками."""
    buttons = [
        [KeyboardButton(text="📚 Список предметов")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    
    if user_id in ADMIN_IDS:
        buttons.insert(1, [KeyboardButton(text="📝 Добавить ДЗ")])
        buttons.insert(2, [KeyboardButton(text="🗑 Удалить ДЗ")])
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_subjects_inline_keyboard() -> InlineKeyboardMarkup:
    """Создаёт inline-клавиатуру со списком предметов."""
    buttons = []
    for num, name in SUBJECTS.items():
        buttons.append([InlineKeyboardButton(
            text=f"{num}. {name}",
            callback_data=f"subject_{num}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def send_file(bot, user_id: int, file_id: str, file_type: str):
    """Отправляет файл пользователю в зависимости от типа."""
    if file_type == "photo":
        await bot.send_photo(user_id, file_id)
    elif file_type == "document":
        await bot.send_document(user_id, file_id)
    elif file_type == "video":
        await bot.send_video(user_id, file_id)
    elif file_type == "audio":
        await bot.send_audio(user_id, file_id)
    elif file_type == "voice":
        await bot.send_voice(user_id, file_id)
    elif file_type == "animation":
        await bot.send_animation(user_id, file_id)

async def send_hw_to_user(
    message,  # Может быть Message или Message из callback
    text: str = None,
    photos: list = None,
    file_id: str = None,
    file_type: str = None,
    reply_markup=None,
    bot=None  # Явно передаём бота для callback
):
    """
    Отправляет ДЗ пользователю в ЛС.
    """
    # Если бот не передан явно — берём из message
    if bot is None:
        bot = message.bot

    # ВАЖНО: используем chat.id, а не from_user.id
    # Для callback.message from_user — это бот, а не пользователь!
    user_id = message.chat.id
    chat_id = message.chat.id
    is_group = message.chat.type in ["group", "supergroup"]

    try:
        # Отправляем фото (для пункта 14 — списки лаб)
        if photos:
            await bot.send_photo(user_id, photos[0])
            if len(photos) > 1:
                await bot.send_photo(user_id, photos[1])

        # Отправляем текст
        if text:
            await bot.send_message(user_id, text, reply_markup=reply_markup)

        # Отправляем прикреплённый файл
        if file_id and file_type:
            await send_file(bot, user_id, file_id, file_type)

        # Если были в группе — уведомляем и удаляем уведомление
        if is_group:
            notify = await message.answer("✅ <b>Отправил в лс!</b>")
            asyncio.create_task(delete_message_later(bot, chat_id, notify.message_id))

    except TelegramBadRequest as e:
        error_text = str(e).lower()
        if "chat not found" in error_text or "bot was blocked" in error_text:
            if is_group:
                notify = await message.answer(
                    "❌ Не могу отправить в ЛС. Напиши мне /start в личные сообщения!"
                )
                asyncio.create_task(delete_message_later(bot, chat_id, notify.message_id))
            else:
                try:
                    await bot.send_message(
                        user_id,
                        "❌ Напиши мне /start, чтобы я мог отправлять тебе ДЗ."
                    )
                except Exception:
                    pass
        else:
            print(f"❌ Ошибка отправки: {e}")
            raise

def truncate_text(text: str, max_len: int = 40) -> str:
    """Обрезает длинный текст и добавляет многоточие."""
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "..."