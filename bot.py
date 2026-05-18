import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обновленный список админов
ADMIN_IDS = [5349346619, 5919988510, 5569374433]
warns = {}

def parse_time(time_str: str):
    if not time_str: return timedelta(hours=1)
    unit = time_str[-1].lower()
    try:
        value = int(time_str[:-1])
        if unit == 's': return timedelta(seconds=value)
        if unit == 'm': return timedelta(minutes=value)
        if unit == 'h': return timedelta(hours=value)
        if unit == 'd': return timedelta(days=value)
    except: return None
    return None

def is_admin(user_id):
    return user_id in ADMIN_IDS

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("🦾 Модератор готов. Лимиты: 30с - 365д.\nКоманды: /mute, /warn, /ban, /unmute")

@dp.message(Command("mute"))
async def mute_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    if not message.reply_to_message:
        return await message.reply("⚠️ Ответь на сообщение нарушителя!")

    args = command.args.split(maxsplit=1) if command.args else []
    time_arg = args[0] if len(args) > 0 else "1h"
    reason = args[1] if len(args) > 1 else "Не указана"

    duration = parse_time(time_arg)
    if not duration:
        return await message.reply("⚠️ Ошибка. Пример: /mute 30s или /mute 1d")

    seconds = duration.total_seconds()
    if seconds < 30:
        duration = timedelta(seconds=30)
    elif seconds > 31536000:
        duration = timedelta(days=365)

    until_date = datetime.now() + duration
    try:
        await bot.restrict_chat_member(
            message.chat.id, 
            message.reply_to_message.from_user.id,
            ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await message.answer(f"🤐 Замучен до: {until_date.strftime('%Y-%m-%d %H:%M')}\n📝 Причина: {reason}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("warn"))
async def warn_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    if not message.reply_to_message:
        return await message.reply("⚠️ Ответь на сообщение!")

    user_id = message.reply_to_message.from_user.id
    reason = command.args if command.args else "Не указана"
    warns[user_id] = warns.get(user_id, 0) + 1

    if warns[user_id] >= 3:
        try:
            await bot.ban_chat_member(message.chat.id, user_id)
            await message.answer(f"🔴 {message.reply_to_message.from_user.first_name} забанен (3/3 варна).\n📝 Причина: {reason}")
            warns[user_id] = 0
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
    else:
        await message.answer(f"⚠️ {message.reply_to_message.from_user.first_name}, варн ({warns[user_id]}/3)!\n📝 Причина: {reason}")

@dp.message(Command("ban"))
async def ban_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    if not message.reply_to_message:
        return await message.reply("⚠️ Ответь на сообщение!")

    reason = command.args if command.args else "Не указана"
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"🔴 Забанен. Причина: {reason}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("unmute"))
async def unmute_handler(message: Message):
    if not is_admin(message.from_user.id): return
    if not message.reply_to_message: return
    try:
        await bot.restrict_chat_member(
            message.chat.id,
            message.reply_to_message.from_user.id,
            ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
        )
        await message.answer("🔊 Размучен.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
