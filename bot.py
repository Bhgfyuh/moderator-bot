import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище варнов (в памяти, при перезагрузке сбросятся)
warns = {}

# Вспомогательная функция для парсинга времени
def parse_time(time_str: str):
    unit = time_str[-1].lower()
    value = int(time_str[:-1])
    if unit == 'm': return timedelta(minutes=value)
    if unit == 'h': return timedelta(hours=value)
    if unit == 'd': return timedelta(days=value)
    return None

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Бот-модератор готов! Доступны: /mute, /unmute, /warn, /ban")

# КОМАНДА МУТ: /mute 10m (ответ на сообщение)
@dp.message(Command("mute"))
async def mute_user(message: Message, command: CommandObject):
    if not message.reply_to_message:
        return await message.reply("Ответь на сообщение нарушителя!")
    
    duration = parse_time(command.args) if command.args else timedelta(hours=1)
    if not duration:
        return await message.reply("Неверный формат! Пример: 10m, 2h, 1d")

    until_date = datetime.now() + duration
    
    try:
        await bot.restrict_chat_member(
            message.chat.id, 
            message.reply_to_message.from_user.id,
            ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await message.answer(f"🤐 {message.reply_to_message.from_user.first_name} замучен до {until_date.strftime('%H:%M:%S')}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# КОМАНДА РАЗМУТ
@dp.message(Command("unmute"))
async def unmute_user(message: Message):
    if not message.reply_to_message:
        return await message.reply("Ответь на сообщение того, кого размутить!")
    
    try:
        await bot.restrict_chat_member(
            message.chat.id,
            message.reply_to_message.from_user.id,
            ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
        )
        await message.answer(f"🔊 {message.reply_to_message.from_user.first_name} снова может говорить.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# КОМАНДА ВАРН (ПРЕДУПРЕЖДЕНИЕ)
@dp.message(Command("warn"))
async def warn_user(message: Message):
    if not message.reply_to_message:
        return await message.reply("Ответь на сообщение нарушителя!")

    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name
    
    warns[user_id] = warns.get(user_id, 0) + 1
    
    if warns[user_id] >= 3:
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.answer(f"🔴 {user_name} получил 3-й варн и был забанен!")
        warns[user_id] = 0
    else:
        await message.answer(f"⚠️ {user_name}, тебе выдан варн! ({warns[user_id]}/3)")

# КОМАНДА БАН
@dp.message(Command("ban"))
async def ban_user(message: Message):
    if not message.reply_to_message:
        return await message.reply("Ответь на сообщение!")
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
