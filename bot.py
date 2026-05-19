import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

# ТВОЙ ТОКЕН
TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# НАСТРОЙКИ
OWNER_ID = 5349346619
ADMIN_IDS = [5349346619, 5919988510, 5569374433]
demoted_admins = set()
warns = {}
help_cooldown = {}
chat_members = {} # База для команды /army

# Вспомогательные функции
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
    return user_id in ADMIN_IDS and user_id not in demoted_admins

# Сборщик участников для /army
@dp.message(lambda m: not m.text or not m.text.startswith('/'))
async def collect_members(message: Message):
    cid = message.chat.id
    if cid not in chat_members: chat_members[cid] = set()
    chat_members[cid].add(message.from_user.id)

# --- КОМАНДЫ ---

@dp.message(Command("help"))
async def help_handler(message: Message):
    uid = message.from_user.id
    now = datetime.now()
    if not is_admin(uid):
        last = help_cooldown.get(uid)
        if last and (now - last).total_seconds() < 300:
            try:
                await bot.restrict_chat_member(message.chat.id, uid, ChatPermissions(can_send_messages=False), until_date=now + timedelta(minutes=20))
                return await message.answer(f"🤫 {message.from_user.first_name} замучен на 20 мин за спам /help.")
            except: return
        help_cooldown[uid] = now

    help_text = (
        "📜 **Команды модерации:**\n"
        "🔹 `/mute [время] [причина]` — Мут (ответ)\n"
        "🔹 `/unmute` — Снять мут (ответ)\n"
        "🔹 `/warn [причина]` — Варн (3/3 = бан)\n"
        "🔹 `/unwarn` — Снять варн (ответ)\n"
        "🔹 `/ban [причина]` — Бан\n"
        "🔹 `/army [текст]` — Сбор (тег всех)\n\n"
        "👑 **Для Лидера:**\n"
        "🔹 `/demote` / `/promote` — Управление админами\n\n"
        "🛡 **СТАРШИЙ СОСТАВ:**\n"
        "👑 Лидер: **Никита**\n"
        "💻 Тех. Админ: **Олег**\n"
        "🎖 Гл. Зам: **Арлан**\n"
        "🥈 Зам: **Ярик**"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("army"))
async def army_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    cid = message.chat.id
    if cid not in chat_members or not chat_members[cid]:
        return await message.answer("📝 База пуста. Пусть все что-то напишут!")
    
    reason = command.args if command.args else "Срочное построение!"
    mentions = [f"[{e}](tg://user?id={uid})" for i, uid in enumerate(chat_members[cid]) for e in [["🎖","🪖","🔫","🛡"][i % 4]]]
    
    text = f"🚨 **ВОЕННЫЕ СБОРЫ!** 🚨\n\n📢 **ПРИКАЗ:** {reason}\n\n👥 **ПРИЗЫВ:** {' '.join(mentions)}"
    msg = await message.answer(text, parse_mode="Markdown")
    try: await bot.pin_chat_message(cid, msg.message_id)
    except: pass

@dp.message(Command("mute"))
async def mute_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    if not message.reply_to_message: return await message.reply("⚠️ Ответь нарушителю!")
    args = command.args.split(maxsplit=1) if command.args else []
    t_arg = args[0] if len(args) > 0 else "1h"
    reason = args[1] if len(args) > 1 else "Не указана"
    dur = parse_time(t_arg)
    if not dur: return await message.reply("⚠️ Пример: /mute 10m")
    sec = dur.total_seconds()
    if sec < 30: dur = timedelta(seconds=30)
    elif sec > 31536000: dur = timedelta(days=365)
    until = datetime.now() + dur
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer(f"🤐 Мут до: {until.strftime('%Y-%m-%d %H:%M')}\n📝 Причина: {reason}")
    except Exception as e: await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("warn"))
async def warn_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    reason = command.args if command.args else "Не указана"
    warns[uid] = warns.get(uid, 0) + 1
    if warns[uid] >= 3:
        try:
            await bot.ban_chat_member(message.chat.id, uid)
            await message.answer(f"🔴 {message.reply_to_message.from_user.first_name} забанен (3/3 варна).")
            warns[uid] = 0
        except Exception as e: await message.answer(f"❌ Ошибка: {e}")
    else:
        await message.answer(f"⚠️ {message.reply_to_message.from_user.first_name}, варн ({warns[uid]}/3)!\n📝 Причина: {reason}")

@dp.message(Command("unwarn"))
async def unwarn_handler(message: Message):
    if not is_admin(message.from_user.id): return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    if uid in warns and warns[uid] > 0:
        warns[uid] -= 1
        await message.answer(f"✅ Снят варн ({warns[uid]}/3)")
    else: await message.answer("😇 Нет варнов.")

@dp.message(Command("ban"))
async def ban_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    if not message.reply_to_message: return
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

@dp.message(Command("demote"))
async def demote_handler(message: Message):
    if message.from_user.id != OWNER_ID or not message.reply_to_message: return
    target = message.reply_to_message.from_user.id
    if target != OWNER_ID:
        demoted_admins.add(target)
        await message.answer(f"🚫 Админ {message.reply_to_message.from_user.first_name} снят.")

@dp.message(Command("promote"))
async def promote_handler(message: Message):
    if message.from_user.id != OWNER_ID or not message.reply_to_message: return
    target = message.reply_to_message.from_user.id
    if target in demoted_admins:
        demoted_admins.
