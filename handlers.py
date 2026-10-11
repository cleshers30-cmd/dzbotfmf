"""
Все обработчики команд и сообщений бота.
"""





from datetime import datetime
from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from config import SUBJECTS, ADMIN_IDS, LAB_PHOTO_1, LAB_PHOTO_2
from states import AddHWStates, DeleteHWStates
from database import add_hw_to_db, get_hw_by_subject, get_hw_by_id, delete_hw_from_db
from utils import (
    send_hw_to_user, 
    truncate_text, 
    get_main_keyboard, 
    get_subjects_inline_keyboard,
    send_file
)

router = Router()
# ==================== БАЗОВЫЕ КОМАНДЫ ====================

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Приветствие и инструкция."""
    text = (
        "👋 <b>Привет! Я бот для домашних заданий.</b>\n\n"
        "Используй кнопки ниже для навигации:\n\n"
        "📚 <b>Список предметов</b> — выбрать предмет и посмотреть ДЗ\n"
        "❓ <b>Помощь</b> — инструкция\n"
    )
    
    if message.from_user.id in ADMIN_IDS:
        text += (
            "\n👨‍🏫 <b>Для ответственных:</b>\n"
            "📝 <b>Добавить ДЗ</b> — добавить новое ДЗ\n"
            "🗑 <b>Удалить ДЗ</b> — удалить ДЗ по ID\n"
        )
    
    text += "\n💡 В группе бот отправит ДЗ тебе в ЛС, чтобы не засорять чат."
    
    await message.answer(
        text,
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@router.message(F.text == "📚 Список предметов")
async def btn_show_subjects(message: types.Message):
    """Показывает список предметов с inline-кнопками."""
    await message.answer(
        "📚 <b>Выбери предмет:</b>",
        reply_markup=get_subjects_inline_keyboard()
    )

@router.message(F.text == "❓ Помощь")
async def btn_help(message: types.Message):
    """Показывает помощь."""
    text = (
        "❓ <b>Помощь</b>\n\n"
        "📚 <b>Список предметов</b> — нажми, чтобы выбрать предмет и посмотреть ДЗ\n"
        "❓ <b>Помощь</b> — эта инструкция\n"
    )
    
    if message.from_user.id in ADMIN_IDS:
        text += (
            "\n👨‍🏫 <b>Для ответственных:</b>\n"
            "📝 <b>Добавить ДЗ</b> — добавить новое ДЗ с файлом\n"
            "🗑 <b>Удалить ДЗ</b> — удалить ДЗ по ID\n"
        )
    
    text += (
        "\n💡 <b>Как это работает:</b>\n"
        "• В группе бот отправит ДЗ тебе в ЛС\n"
        "• Через 10 секунд сообщение в группе удалится\n"
        "• Каждый должен написать /start боту в ЛС хотя бы раз"
    )
    
    await message.answer(text)

# ==================== ДОБАВЛЕНИЕ ДЗ ====================

@router.message(F.text == "📝 Добавить ДЗ")
async def btn_add_hw(message: types.Message, state: FSMContext):
    """Запуск FSM для добавления ДЗ (только для админов)."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет прав для добавления ДЗ.")
        return

    await message.answer(
        "📝 <b>Добавление ДЗ</b>\n\nВыберите номер предмета:",
        reply_markup=get_subjects_inline_keyboard()
    )
    await state.set_state(AddHWStates.waiting_for_subject)

@router.message(AddHWStates.waiting_for_subject, F.text == "/cancel")
async def cancel_add_subject(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Добавление отменено.",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@router.message(AddHWStates.waiting_for_date, F.text == "/cancel")
async def cancel_add_date(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Добавление отменено.",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@router.message(AddHWStates.waiting_for_text, F.text == "/cancel")
async def cancel_add_text(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Добавление отменено.",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@router.message(AddHWStates.waiting_for_file, F.text == "/cancel")
async def cancel_add_file(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Добавление отменено.",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@router.message(AddHWStates.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        return
    
    await state.update_data(date=message.text.strip())
    await message.answer(
        "📝 Теперь отправьте <b>текст домашнего задания</b>:\n"
        "<i>Или /cancel для отмены</i>"
    )
    await state.set_state(AddHWStates.waiting_for_text)

@router.message(AddHWStates.waiting_for_text, F.text)
async def process_text(message: types.Message, state: FSMContext):
    """После ввода текста переходим к ожиданию файла."""
    if message.text == "/cancel":
        return
    
    await state.update_data(text=message.text)
    await message.answer(
        "📎 Теперь вы можете <b>прикрепить файл</b> к ДЗ:\n"
        "• Фото\n"
        "• Документ (PDF, Word и т.д.)\n"
        "• Видео\n"
        "• Аудио\n\n"
        "Отправьте файл или напишите /skip, чтобы сохранить без файла.\n"
        "<i>Или /cancel для отмены</i>"
    )
    await state.set_state(AddHWStates.waiting_for_file)

# === Обработчики файлов в состоянии waiting_for_file ===

@router.message(AddHWStates.waiting_for_file, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    """Обработка прикреплённого фото."""
    file_id = message.photo[-1].file_id
    await state.update_data(file_id=file_id, file_type="photo")
    await _save_hw(message, state)

@router.message(AddHWStates.waiting_for_file, F.document)
async def process_document(message: types.Message, state: FSMContext):
    """Обработка прикреплённого документа."""
    file_id = message.document.file_id
    await state.update_data(file_id=file_id, file_type="document")
    await _save_hw(message, state)

@router.message(AddHWStates.waiting_for_file, F.video)
async def process_video(message: types.Message, state: FSMContext):
    """Обработка прикреплённого видео."""
    file_id = message.video.file_id
    await state.update_data(file_id=file_id, file_type="video")
    await _save_hw(message, state)

@router.message(AddHWStates.waiting_for_file, F.audio)
async def process_audio(message: types.Message, state: FSMContext):
    """Обработка прикреплённого аудио."""
    file_id = message.audio.file_id
    await state.update_data(file_id=file_id, file_type="audio")
    await _save_hw(message, state)

@router.message(AddHWStates.waiting_for_file, F.voice)
async def process_voice(message: types.Message, state: FSMContext):
    """Обработка голосового сообщения."""
    file_id = message.voice.file_id
    await state.update_data(file_id=file_id, file_type="voice")
    await _save_hw(message, state)

@router.message(AddHWStates.waiting_for_file, F.animation)
async def process_animation(message: types.Message, state: FSMContext):
    """Обработка GIF-анимации."""
    file_id = message.animation.file_id
    await state.update_data(file_id=file_id, file_type="animation")
    await _save_hw(message, state)

@router.message(AddHWStates.waiting_for_file, F.text == "/skip")
async def skip_file(message: types.Message, state: FSMContext):
    """Пропуск прикрепления файла."""
    await state.update_data(file_id=None, file_type=None)
    await _save_hw(message, state)

@router.message(AddHWStates.waiting_for_file)
async def invalid_file_input(message: types.Message):
    """Если отправили что-то неподходящее."""
    await message.answer(
        "⚠️ Я жду файл (фото, документ, видео, аудио) или команду /skip.\n"
        "<i>Или /cancel для отмены</i>"
    )

async def _save_hw(message: types.Message, state: FSMContext):
    """Сохраняет ДЗ в базу данных и завершает FSM."""
    data = await state.get_data()
    add_hw_to_db(
        subject=data['subject'],
        date=data['date'],
        text=data['text'],
        file_id=data.get('file_id'),
        file_type=data.get('file_type')
    )
    await state.clear()

    subj_name = SUBJECTS[data['subject']]
    has_file = data.get('file_id') is not None

    file_info = ""
    if has_file:
        file_type_names = {
            "photo": "📷 Фото",
            "document": "📄 Документ",
            "video": "🎬 Видео",
            "audio": "🎵 Аудио",
            "voice": "🎤 Голосовое",
            "animation": "🎞 GIF"
        }
        file_info = f"\n📎 Файл: {file_type_names.get(data['file_type'], data['file_type'])}"

    await message.answer(
        f"✅ <b>ДЗ добавлено!</b>\n\n"
        f"📚 Предмет: {subj_name}\n"
        f"📅 Дата: {data['date']}\n"
        f"📝 Текст: {data['text']}"
        f"{file_info}",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

# ==================== ПРОСМОТР ДЗ ====================

@router.callback_query(F.data.startswith("subject_"))
async def callback_subject(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора предмета через inline-кнопку."""
    print(f"🔍 Callback subject получен: {callback.data}")
    
    try:
        subj_num = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка выбора предмета")
        return

    if subj_num not in SUBJECTS:
        await callback.answer("❌ Предмет не найден")
        return

    await callback.answer()

    # Если мы в процессе добавления ДЗ
    current_state = await state.get_state()
    if current_state == AddHWStates.waiting_for_subject:
        await state.update_data(subject=subj_num)
        today = datetime.now().strftime("%d.%m")
        await callback.message.answer(
            f"✅ Выбрано: <b>{SUBJECTS[subj_num]}</b>\n\n"
            f"Введите дату (например: <code>{today}</code>):\n"
            "<i>Или /cancel для отмены</i>"
        )
        await state.set_state(AddHWStates.waiting_for_date)
        return

    # Иначе показываем ДЗ
 
    # === Остальные предметы: ДЗ из БД ===
    rows = get_hw_by_subject(subj_num)
    subj_name = SUBJECTS[subj_num]

    if not rows:
        text = (
            f"📚 <b>{subj_name}</b>\n\n"
            "🤷 Пока нет добавленных домашних заданий."
        )
        await send_hw_to_user(
            callback.message, 
            text=text,
            bot=callback.bot  # ← ВАЖНО
        )
        return

    # Самое свежее ДЗ
    latest_id, latest_date, latest_text, latest_file_id, latest_file_type = rows[0]
    past_rows = rows[1:]

    # Формируем текст
    parts = [f"📚 <b>{subj_name}</b>\n"]

    # Создаём кнопки для прошлых ДЗ
    buttons = []
    
    if past_rows:
        parts.append("📜 <b>Прошлые ДЗ:</b>")
        for hw_id, date, txt, f_id, f_type in past_rows:
            short = truncate_text(txt.replace("\n", " "), 30)
            file_icon = " 📎" if f_id else ""
            parts.append(f"┣ <b>[{date}]</b> {short}{file_icon}")
            buttons.append([InlineKeyboardButton(
                text=f"📖 ДЗ от {date}",
                callback_data=f"view_{hw_id}"
            )])
        parts.append("")

    parts.append(f"📝 <b>Последнее ДЗ:</b>")
    parts.append(f"📅 <i>{latest_date}</i>")
    parts.append(f"📄 {latest_text}")
    if latest_file_id:
        parts.append("📎 <i>Есть прикреплённый файл</i>")

    # Кнопка для просмотра последнего ДЗ
    buttons.insert(0, [InlineKeyboardButton(
        text=f"📖 Открыть последнее ДЗ",
        callback_data=f"view_{latest_id}"
    )])

    # Кнопка назад к списку предметов
    buttons.append([InlineKeyboardButton(
        text="◀️ Назад к списку предметов",
        callback_data="back_to_subjects"
    )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await send_hw_to_user(
        callback.message,
        text="\n".join(parts),
        file_id=latest_file_id,
        file_type=latest_file_type,
        reply_markup=keyboard,
        bot=callback.bot  # ← ВАЖНО: передаём бота явно
    )
    print(f"✅ ДЗ по предмету {subj_num} отправлено")

@router.callback_query(F.data.startswith("view_"))
async def callback_view_hw(callback: types.CallbackQuery):
    """Обработка нажатия на кнопку просмотра конкретного ДЗ."""
    print(f"🔍 Callback view получен: {callback.data}")
    
    try:
        hw_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка")
        return

    await callback.answer()

    row = get_hw_by_id(hw_id)
    if not row:
        print(f"❌ ДЗ с ID {hw_id} не найдено")
        await callback.bot.send_message(
            callback.from_user.id,
            f"⚠️ ДЗ с ID <b>{hw_id}</b> не найдено."
        )
        return

    print(f"✅ ДЗ с ID {hw_id} найдено")
    _, subj, date, text, file_id, file_type = row
    subj_name = SUBJECTS.get(subj, "Удалённый предмет")

    file_info = "\n📎 <i>Есть прикреплённый файл</i>" if file_id else ""

    full_text = (
        f"📚 <b>{subj_name}</b>\n"
        f"📅 <b>Дата:</b> {date}\n"
        f"🆔 <b>ID:</b> {hw_id}{file_info}\n\n"
        f"📄 {text}"
    )

    # Кнопка назад
    buttons = [[InlineKeyboardButton(
        text="◀️ Назад",
        callback_data=f"subject_{subj}"
    )]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    # ВАЖНО: отправляем напрямую в ЛС пользователя через callback.bot
    try:
        if file_id and file_type:
            from utils import send_file
            await send_file(callback.bot, callback.from_user.id, file_id, file_type)
        await callback.bot.send_message(
            callback.from_user.id,
            full_text,
            reply_markup=keyboard
        )
        print(f"✅ ДЗ с ID {hw_id} отправлено в ЛС")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        await callback.answer("❌ Ошибка отправки", show_alert=True)

@router.callback_query(F.data == "back_to_subjects")
async def callback_back_to_subjects(callback: types.CallbackQuery):
    """Возврат к списку предметов."""
    await callback.answer()
    await callback.bot.send_message(
        callback.from_user.id,
        "📚 <b>Выбери предмет:</b>",
        reply_markup=get_subjects_inline_keyboard()
    )

# ==================== УДАЛЕНИЕ ДЗ ====================

# ==================== УДАЛЕНИЕ ДЗ ====================

@router.message(F.text == "🗑 Удалить ДЗ")
async def btn_del_hw(message: types.Message, state: FSMContext):
    """Запуск FSM для удаления ДЗ (только для админов)."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет прав для удаления ДЗ.")
        return

    await message.answer(
        "🗑 <b>Удаление ДЗ</b>\n\n"
        "Введите <b>ID</b> записи, которую нужно удалить.\n"
        "<i>ID можно узнать через список предметов</i>\n\n"
        "Или /cancel для отмены."
    )
    await state.set_state(DeleteHWStates.waiting_for_id)


@router.message(DeleteHWStates.waiting_for_id, F.text == "/cancel")
async def cancel_delete_by_command(message: types.Message, state: FSMContext):
    """Отмена через /cancel на этапе ввода ID."""
    await state.clear()
    await message.answer(
        "❌ Удаление отменено.",
        reply_markup=get_main_keyboard(message.from_user.id)
    )


@router.message(DeleteHWStates.waiting_for_id)
async def process_delete_id(message: types.Message, state: FSMContext):
    """Получаем ID ДЗ и показываем превью для подтверждения."""
    try:
        hw_id = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Введите число (ID записи).")
        return

    row = get_hw_by_id(hw_id)
    if not row:
        await message.answer(
            f"⚠️ ДЗ с ID <b>{hw_id}</b> не найдено.\n"
            "Попробуйте ещё раз или /cancel для отмены."
        )
        return

    _, subj, date, text, file_id, file_type = row
    subj_name = SUBJECTS.get(subj, "Удалённый предмет")
    file_info = "\n📎 Есть прикреплённый файл" if file_id else ""

    # Сохраняем ID в FSM
    await state.update_data(hw_id=hw_id)
    
    # ⚠️ ВАЖНО: переключаемся в НОВОЕ состояние для подтверждения!
    await state.set_state(DeleteHWStates.waiting_for_confirm)
    
    await message.answer(
        f"🗑 Вы хотите удалить запись:\n\n"
        f"📚 {subj_name}\n"
        f"📅 {date}\n"
        f"📄 {truncate_text(text, 100)}{file_info}\n\n"
        f"Отправьте <b>ДА</b> для подтверждения или <b>НЕТ</b> для отмены."
    )


@router.message(DeleteHWStates.waiting_for_confirm, F.text.lower().in_({"да", "yes", "да ", "yes "}))
async def confirm_delete(message: types.Message, state: FSMContext):
    """Подтверждение удаления."""
    data = await state.get_data()
    hw_id = data.get('hw_id')

    if not hw_id:
        await state.clear()
        await message.answer(
            "⚠️ Сессия устарела. Начните заново.",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return

    if delete_hw_from_db(hw_id):
        await message.answer(
            f"✅ ДЗ с ID <b>{hw_id}</b> успешно удалено.",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
    else:
        await message.answer(
            f"⚠️ Не удалось удалить запись с ID <b>{hw_id}</b>.",
            reply_markup=get_main_keyboard(message.from_user.id)
        )

    await state.clear()


@router.message(DeleteHWStates.waiting_for_confirm, F.text.lower().in_({"нет", "no", "/cancel", "нет ", "no "}))
async def cancel_delete(message: types.Message, state: FSMContext):
    """Отмена удаления."""
    await state.clear()
    await message.answer(
        "❌ Удаление отменено.",
        reply_markup=get_main_keyboard(message.from_user.id)
    )


@router.message(DeleteHWStates.waiting_for_confirm)
async def invalid_confirm_input(message: types.Message, state: FSMContext):
    """Если ввели что-то непонятное вместо ДА/НЕТ."""
    await message.answer(
        "⚠️ Я жду ответ <b>ДА</b> или <b>НЕТ</b>.\n"
        "Или /cancel для отмены."
    )