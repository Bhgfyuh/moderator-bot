import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Твой личный ID (Главный админ)
OWNER_ID = 5349346619
# Список доверенных админов
ADMIN_IDS = [5349346619, 5919988510, 5569374433]
# Черный список для админов, которых ты "снял"
demoted_admins = set()

warns = {}
help_cooldown = {}

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
    # Админ должен быть в списке И НЕ быть в черном списке
    return user_id in ADMIN_IDS and user_id not in demoted_admins

# --- ЛИЧНЫЕ КОМАНДЫ ВЛАДЕЛЬЦА ---
@dp.message(Command("demote"))
async def demote_admin(message: Message):
    if message.from_user.id != OWNER_ID: return
    if not message.reply_to_message:
        return await message.reply("⚠️ Ответь на сообщение админа, которого хочешь снять!")
    
    target_id = message.reply_to_message.from_user.id
    if target_id == OWNER_ID:
        return await message.reply("Сам себя снять не можешь, бро.")
    
    demoted_admins.add(target_id)
    await message.answer(f"🚫 Доступ к командам для {message.reply_to_message.from_user.first_name} заблокирован.")

@dp.message(Command("promote"))
async def promote_admin(message: Message):
    if message.from_user.id != OWNER_ID: return
    if not message.reply_to_message:
        return await message.reply("⚠️ Ответь на сообщение того, кому вернуть доступ!")
    
    target_id = message.reply_to_message.from_user.id
    if target_id in demoted_admins:
        demoted_admins.remove(target_id)
        await message.answer(f"✅ Доступ для {message.reply_to_message.from_user.first_name} восстановлен.")
    else:
        await message.answer("Этот пользователь и так не в черном списке.")
# -------------------------------

@dp.message(Command("help"))
async def help_handler(message: Message):
    user_id = message.from_user.id
    now = datetime.now()

    if not is_admin(user_id):
        last_call = help_cooldown.get(user_id)
        if last_call and (now - last_call).total_seconds() < 300:
            try:
                until_date = now + timedelta(minutes=20)
                await bot.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=False), until_date=until_date)
                return await message.answer(f"🤫 {message.from_user.first_name} замучен на 20 минут за спам /help.")
            except: return
        help_cooldown[user_id] = now

    help_text = (
        "📜 **Справка по командам:**\n\n"
        "🔹 `/mute [время] [причина]` — Мут (ответ)\n"
        "🔹 `/unmute` — Снять мут (ответ)\n"
        "🔹 `/warn [причина]` — Варн (3/3 = бан)\n"
        "🔹 `/unwarn` — Снять варн (ответ)\n"
        "🔹 `/ban [причина]` — Бан навсегда\n\n"
        "👑 **Для Лидера:**\n"
        "🔹 `/demote` — Снять админа (ответ)\n"
        "🔹 `/promote` — Вернуть админа (ответ)\n\n"
        "🛡 **СТАРШИЙ СОСТАВ:**\n"
        "👑 Лидер: **Никита**\n"
        "💻 Тех. Админ: **Олег**\n"
        "🎖 Гл. Зам: **Арлан**\n"
        "🥈 Зам: **Ярик**"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("🦾 Бот активен! Список команд: /help")

@dp.message(Command("mute"))
async def mute_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    if not message.reply_to_message: return await message.reply("⚠️ Ответь нарушителю!")
    args = command.args.split(maxsplit=1) if command.args else []
    time_arg = args[0] if len(args) > 0 else "1h"
    reason = args[1] if len(args) > 1 else "Не указана"
    duration = parse_time(time_arg)
    if not duration: return await message.reply("⚠️ Пример: /mute 10m")
    seconds = duration.total_seconds()
    if seconds < 30: duration = timedelta(seconds=30)
    elif seconds > 31536000: duration = timedelta(days=365)
    until_date = datetime.now() + duration
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False), until_date=until_date)
        await message.answer(f"🤐 Мут до: {until_date.strftime('%Y-%m-%d %H:%M')}\n📝 Причина: {reason}")
    except Exception as e: await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("warn"))
async def warn_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    if not message.reply_to_message: return await message.reply("⚠️ Ответь нарушителю!")
    user_id = message.reply_to_message.from_user.id
    reason = command.args if command.args else "Не указана"
    warns[user_id] = warns.get(user_id, 0) + 1
    if warns[user_id] >= 3:
        try:
            await bot.ban_chat_member(message.chat.id, user_id)
            await message.answer(f"🔴 {message.reply_to_message.from_user.first_name} забанен (3/3 варна).\n📝 Причина: {reason}")
            warns[user_id] = 0
        except Exception as e: await message.answer(f"❌ Ошибка: {e}")
    else:
        await message.answer(f"⚠️ {message.reply_to_message.from_user.first_name}, варн ({warns[user_id]}/3)!\n📝 Причина: {reason}")

@dp.message(Command("unwarn"))
async def unwarn_handler(message: Message):
    if not is_admin(message.from_user.id): return
    if not message.reply_to_message: return await message.reply("⚠️ Ответь нарушителю!")
    user_id = message.reply_to_message.from_user.id
    if user_id in warns and warns[user_id] > 0:
        warns[user_id] -= 1
        await message.answer(f"✅ У {message.reply_to_message.from_user.first_name} снят варн ({warns[user_id]}/3)")
    else: await message.answer("😇 Нет варнов.")

@dp.message(Command("ban"))
async def ban_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    if not message.reply_to_message: return await message.reply("⚠️ Ответь нарушителю!")
    reason = command.args if command.args else "Не указана"
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"🔴 Забанен. Причина: {reason}")
    except Exception as e: await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("unmute"))
async def unmute_handler(message: Message):
    if not is_admin(message.from_user.id): return
    if not message.reply_to_message: return
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
        await message.answer("🔊 Размучен.")
    except Exception as e: await message.answer(f"❌ Ошибка: {e}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
