import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command

# ТОКЕН (строго в кавычках)
TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Команда старт для проверки
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Бот запущен! Я готов модерировать чат.")

# Простая модерация: Мут
@dp.message(Command("mute"), F.reply_to_message)
async def mute(message: Message):
    # Тут можно добавить проверку на админа позже
    await message.chat.restrict(message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False))
    await message.answer("🤐 Пользователь замучен.")

async def main():
    # Удаляем вебхуки, чтобы не было конфликтов
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот вышел в онлайн!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
