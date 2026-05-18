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

# КОМАНДА HELP (Доступна всем)
@dp.message(Command("help"))
async def help_handler(message: Message):
    help_text = (
        "📜 **Справка по командам модерации:**\n\n"
        "🔹 `/mute [время] [причина]` — Ограничить чат (ответ на сообщение).\n"
        "   _Пример: /mute 10m спам_\n"
        "🔹 `/unmute` — Снять ограничения (ответ на сообщение).\n"
        "🔹 `/warn [причина]` — Выдать предупреждение (3/3 = бан).\n"
        "   _Пример: /warn мат_\n"
        "🔹 `/ban [причина]` — Забанить навсегда.\n"
        "   _Пример: /ban читы_\n\n"
        "⏳ Лимиты мута: от 30с до 365д.\n"
        "━━━━━━━━━━━━━━━\n"
        "🛡 **СТАРШИЙ СОСТАВ:**\n"
        "👑 Лидер: **Никита**\n"
        "💻 Тех. Админ: **Олег**\n"
        "🎖 Гл. Зам: **Арлан**\n"
        "🥈 Зам: **Ярик**"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("🦾 Модератор активен! Напиши /help, чтобы увидеть список команд и состав администрации.")

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
