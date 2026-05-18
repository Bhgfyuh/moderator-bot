import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command

TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Команда МУТ (просто отвечает, чтобы проверить связь)
@dp.message(Command("mute"))
async def mute_handler(message: Message):
    if not message.reply_to_message:
        return await message.reply("Нужно ответить на сообщение того, кого мутим!")
    
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await message.answer(f"🤐 {message.reply_to_message.from_user.first_name} замучен.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# Команда БАН
@dp.message(Command("ban"))
async def ban_handler(message: Message):
    if not message.reply_to_message:
        return await message.reply("Ответь на сообщение нарушителя!")
    
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"🔴 {message.reply_to_message.from_user.first_name} забанен!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
