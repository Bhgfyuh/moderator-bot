import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command

# Твой токен
TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Команда старт
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("✅ Бот запущен на новой версии aiogram 3.x!")

# Команда БАН
@dp.message(Command("ban"), F.reply_to_message)
async def ban_handler(message: Message):
    await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
    await message.answer(f"🔴 Пользователь забанен!")

async def main():
    # Очистка старых сообщений
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот в сети!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
