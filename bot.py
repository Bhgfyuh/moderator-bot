import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command

# ТВОЙ ТОКЕН
TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Простая проверка: отвечает на /start
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("✅ Бот запущен на версии 3.x и готов к работе!")

# Команда МУТ (ответом на сообщение)
@dp.message(Command("mute"), F.reply_to_message)
async def mute_handler(message: Message):
    # Ограничиваем отправку сообщений
    await bot.restrict_chat_member(
        chat_id=message.chat.id,
        user_id=message.reply_to_message.from_user.id,
        permissions=ChatPermissions(can_send_messages=False)
    )
    await message.answer(f"🤐 {message.reply_to_message.from_user.first_name} в муте.")

# Команда БАН (ответом на сообщение)
@dp.message(Command("ban"), F.reply_to_message)
async def ban_handler(message: Message):
    await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
    await message.answer(f"🔴 {message.reply_to_message.from_user.first_name} забанен!")

async def main():
    # Удаляем старые обновления, чтобы бот не спамил при запуске
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот вышел в онлайн!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
