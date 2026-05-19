import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher()

ADMIN_IDS = [5349346619, 5919988510, 5569374433]
warns = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS

def parse_time(time_str: str, min_sec: int):
    unit = time_str[-1].lower()
    try:
        val = int(time_str[:-1])
        if unit == 's': res = timedelta(seconds=val)
        elif unit == 'm': res = timedelta(minutes=val)
        elif unit == 'h': res = timedelta(hours=val)
        elif unit == 'd': res = timedelta(days=val)
        else: return timedelta(seconds=min_sec)
        return max(timedelta(seconds=min_sec), min(res, timedelta(days=365)))
    except: return timedelta(seconds=min_sec)

# --- ХЕЛП ---
@dp.message(Command("help"))
async def help_cmd(message: Message):
    text = (
        "⚔️ **ШТАБ IRON EMPIRE**\n\n"
        "🛡 **МОДЕРАЦИЯ (ответом на сообщение):**\n"
        "🤐 `/mute [время] [причина]` (от 30с)\n"
        "🔊 `/unmute` — снять мут\n"
        "⚠️ `/warn [причина]` — выдать варн\n"
        "✅ `/unwarn` — снять варн\n"
        "💀 `/ban [время] [причина]` (от 1с, 0=навсегда)\n"
        "🔓 `/unban [ID или ответом]` — разбан\n"
    )
    await message.answer(text, parse_mode="Markdown")

# --- КОМАНДЫ ---

@dp.message(Command("mute"))
async def mute_cmd(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    args = command.args.split(maxsplit=1) if command.args else ["1h", "Без причины"]
    time_str = args[0]
    reason = args[1] if len(args) > 1 else "Без причины"
    until = datetime.now() + parse_time(time_str, 30)
    await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False), until_date=until)
    await message.answer(f"🤐 **Мут:** {message.reply_to_message.from_user.first_name}\n⏰ **Срок:** {time_str}\n📝 **Причина:** {reason}")

@dp.message(Command("unmute"))
async def unmute_cmd(message: Message):
    if is_admin(message.from_user.id) and message.reply_to_message:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
        await message.answer("🔊 Мут снят.")

@dp.message(Command("ban"))
async def ban_cmd(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    args = command.args.split(maxsplit=1) if command.args else ["0", "Без причины"]
    time_str = args[0]
    reason = args[1] if len(args) > 1 else "Без причины"
    until = (datetime.now() + parse_time(time_str, 1)) if time_str != "0" else None
    await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id, until_date=until)
    await message.answer(f"💀 **Бан:** {message.reply_to_message.from_user.first_name}\n⏰ **Срок:** {time_str if time_str!='0' else 'Навсегда'}\n📝 **Причина:** {reason}")

@dp.message(Command("unban"))
async def unban_cmd(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    target_id = message.reply_to_message.from_user.id if message.reply_to_message else (int(command.args) if command.args and command.args.isdigit() else None)
    if target_id:
        try:
            await bot.unban_chat_member(message.chat.id, target_id, only_if_banned=True)
            await message.answer(f"🔓 Пользователь {target_id} разбанен.")
        except Exception as e: await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("warn"))
async def warn_cmd(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    reason = command.args if command.args else "Без причины"
    warns[uid] = warns.get(uid, 0) + 1
    if warns[uid] >= 3:
        await bot.ban_chat_member(message.chat.id, uid)
        await message.answer(f"🔴 **Бан (3/3 варна):** {message.reply_to_message.from_user.first_name}")
        warns[uid] = 0
    else: await message.answer(f"⚠️ **Варн:** {message.reply_to_message.from_user.first_name} ({warns[uid]}/3)\n📝 **Причина:** {reason}")

@dp.message(Command("unwarn"))
async def unwarn_cmd(message: Message):
    if is_admin(message.from_user.id) and message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        warns[uid] = max(0, warns.get(uid, 0) - 1)
        await message.answer(f"✅ Варн снят. Счёт: {warns[uid]}/3")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
