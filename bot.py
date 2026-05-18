from aiogram import Bot, Dispatcher, executor, types
import asyncio

# ТВОЙ ТОКЕН
TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Команда старт
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("✅ Бот на связи! Модерация активна.")

# Команда БАН (ответ на сообщение)
@dp.message_handler(commands=['ban'], is_chat_admin=True)
async def ban_user(message: types.Message):
    if not message.reply_to_message:
        return await message.reply("Эта команда должна быть ответом на сообщение!")
    
    await bot.kick_chat_member(message.chat.id, message.reply_to_message.from_user.id)
    await message.answer(f"🔴 Пользователь {message.reply_to_message.from_user.first_name} забанен!")

# Команда МУТ
@dp.message_handler(commands=['mute'], is_chat_admin=True)
async def mute_user(message: types.Message):
    if not message.reply_to_message:
        return await message.reply("Ответь на сообщение того, кого хочешь замутить.")
    
    await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_send_messages=False)
    await message.answer(f"🤐 {message.reply_to_message.from_user.first_name} теперь молчит.")

if __name__ == '__main__':
    print("Бот запущен через старую добрую версию!")
    executor.start_polling(dp, skip_updates=True)
