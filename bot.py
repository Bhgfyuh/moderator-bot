import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- СПИСОК АДМИНИСТРАТОРОВ ---
ADMIN_IDS = [5349346619, 5919988510]
# ------------------------------

warns = {}

def parse_time(time_str: str):
    if not time_str: return timedelta(hours=1)
    unit = time_str[-1].lower()
    try:
        value = int(time_str[:-1])
    except ValueError:
        return None
    if unit == 'm': return timedelta(minutes=value)
    if unit == 'h': return timedelta(hours=value)
    if unit == 'd': return timedelta(days=value)
    return None

def admin_only(func):
    async def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id in ADMIN_IDS:
            return await func(message, *args, **kwargs)
        return
    return wrapper

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Бот активен. Доступ разрешен только админам из списка.")

@dp.message(Command("mute"))
@admin_only
async def mute_user(message: Message, command: CommandObject):
    if not message.reply_to_message:
        return await message.reply("Ответь на сообщение нарушителя!")
    duration = parse_time(command.args)
    if not duration:
        return await message.reply("Формат: /mute 10m, 2h, 1d")
    until_date = datetime.now() + duration
    try:
        await bot.restrict_chat_member(
            message.chat.id, 
            message.reply_to_message.from_user.id,
            ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await message.answer(f"🤐 Мут до: {until_date.strftime('%Y-%m-%d %H:%M')}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("unmute"))
@admin_only
async def unmute_user(message: Message):
    if not message.reply_to_message:
        return await message.reply("Ответь на сообщение!")
    try:
        await bot.restrict_chat_member(
            message.chat.id,
            message.reply_to_message.from_user.id,
            ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
        )
        await message.answer(f"🔊 Размучен.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("warn"))
@admin_only
async def warn_user(message: Message):
    if not message.reply_to_message:
        return await message.reply("Ответь на сообщение!")
    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name
    warns[user_id] = warns.get(user_id, 0) + 1
    if warns[user_id] >= 3:
        await bot.ban_chat_member(message.chat.id, user_id)
        await message.answer(f"🔴 {user_name} забанен за 3 варна.")
        warns[user_id] = 0
    else:
        await message.answer(f"⚠️ {user_name}, варн ({warns[user_id]}/3)")

@dp.message(Command("ban"))
@admin_only
async def ban_user(message: Message):
    if not message.reply_to_message:
        return await message.reply("Ответь на сообщение!")
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"🔴 Забанен.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
