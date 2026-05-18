import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command

# ТОКЕН
TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Команда старт
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("✅ Бот успешно запущен на версии 3.x!")

# Команда МУТ (ответом на сообщение)
@dp.message(Command("mute"), F.reply_to_message)
async def mute_handler(message: Message):
    await bot.restrict_chat_member(
        chat_id=message.chat.id,
        user_id=message.reply_to_message.from_user.id,
        permissions=ChatPermissions(can_send_messages=False)
    )
    await message.answer(f"🤐 {message.reply_to_message.from_user.first_name} теперь молчит.")

# Команда БАН (ответом на сообщение)
@dp.message(Command("ban"), F.reply_to_message)
async def ban_handler(message: Message):
    await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
    await message.answer(f"🔴 {message.reply_to_message.from_user.first_name} забанен!")

async def main():
    # Очистка очереди сообщений
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот вышел в онлайн!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
