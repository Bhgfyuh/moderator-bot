import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

def parse_time(time_str: str):
    if not time_str: return timedelta(hours=1)
    unit = time_str[-1].lower()
    try:
        value = int(time_str[:-1])
        if unit == 'm': return timedelta(minutes=value)
        if unit == 'h': return timedelta(hours=value)
        if unit == 'd': return timedelta(days=value)
    except: return None
    return None

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Бот онлайн! Попробуй ответить на чьё-то сообщение командой /mute 1m")

@dp.message(Command("mute"))
async def mute_user(message: Message, command: CommandObject):
    # Проверка: является ли отправитель админом по списку
    if message.from_user.id not in [5349346619, 5919988510]:
        return # Если пишет не ты и не друг — игнор

    if not message.reply_to_message:
        return await message.reply("⚠️ Нужно ответить на сообщение нарушителя!")
    
    duration = parse_time(command.args)
    if not duration:
        return await message.reply("⚠️ Пример: /mute 5m")

    until_date = datetime.now() + duration
    
    try:
        await bot.restrict_chat_member(
            message.chat.id, 
            message.reply_to_message.from_user.id,
            ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await message.answer(f"🤐 Замучен до {until_date.strftime('%H:%M')}")
    except Exception as e:
        await message.answer(f"❌ Ошибка прав: {e}\n(Убедись, что бот — админ!)")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
