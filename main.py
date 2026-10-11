"""
Главный файл запуска бота.
"""

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, SUBJECTS, ADMIN_IDS
from database import init_db
from handlers import router

# Создаём бота и диспетчер
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Подключаем роутер с хендлерами
dp.include_router(router)

async def main():
    """Главная функция запуска."""
    # Инициализируем базу данных
    init_db()
    
    print("=" * 50)
    print("✅ Бот успешно запущен!")
    print(f"📚 Предметов в списке: {len(SUBJECTS)}")
    print(f"👨‍🏫 Админов: {len(ADMIN_IDS)}")
    print("=" * 50)
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Бот остановлен.")