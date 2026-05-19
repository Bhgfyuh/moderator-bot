import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

# Настройка логирования для отслеживания ошибок
logging.basicConfig(level=logging.INFO)

TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КОНФИГУРАЦИЯ ---
OWNER_ID = 5349346619
ADMIN_IDS = [5349346619, 5919988510, 5569374433]
demoted_admins = set()
warns = {}
help_cooldown = {}
chat_members = {}

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

# Сборщик участников для /army (те, кто пишут сообщения)
@dp.message(F.chat.type.in_({"group", "supergroup"}), ~F.text.startswith('/'))
async def collect_members(message: Message):
    cid = message.chat.id
    if cid not in chat_members: chat_members[cid] = set()
    chat_members[cid].add(message.from_user.id)

# --- КОМАНДЫ ---

@dp.message(Command("help"))
async def help_handler(message: Message):
    uid = message.from_user.id
    now = datetime.now()
    
    # Анти-спам для обычных пользователей
    if not is_admin(uid):
        last = help_cooldown.get(uid)
        if last and (now - last).total_seconds() < 300:
            try:
                until = now + timedelta(minutes=20)
                await bot.restrict_chat_member(message.chat.id, uid, ChatPermissions(can_send_messages=False), until_date=until)
                return await message.answer(f"🤫 {message.from_user.first_name} замучен на 20 мин за спам /help.")
            except: return
        help_cooldown[uid] = now

    help_text = (
        "📜 **СПРАВКА ПО КОМАНДАМ:**\n\n"
        "🔹 `/mute [время] [причина]` — Мут (ответ на смс).\n"
        "🔹 `/unmute` — Снять мут (ответ на смс).\n"
        "🔹 `/warn [причина]` — Выдать варн (3/3 = бан).\n"
        "🔹 `/unwarn` — Снять 1 варн (ответ на смс).\n"
        "🔹 `/ban [причина]` — Забанить (ответ на смс).\n"
        "🔹 `/army [текст]` — Военные сборы (тег всех).\n\n"
        "👑 **ДЛЯ ЛИДЕРА:**\n"
        "🔹 `/demote` — Снять права админа (ответ).\n"
        "🔹 `/promote` — Вернуть права админа (ответ).\n\n"
        "━━━━━━━━━━━━━━━\n"
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
        return await message.answer("📝 База пуста. Пусть пацаны напишут что-нибудь!")
    
    reason = command.args if command.args else "Срочное построение!"
    emojis = ["🎖","🪖","🔫","🛡"]
    # Берем до 50 участников, чтобы избежать блокировок Telegram
    mentions = [f"[{emojis[i % 4]}](tg://user?id={uid})" for i, uid in enumerate(list(chat_members[cid])[:50])]
    
    text = f"🚨 **ВОЕННЫЕ СБОРЫ!** 🚨\n\n📢 **ПРИКАЗ:** {reason}\n\n👥 **ПРИЗЫВ:** {' '.join(mentions)}"
    try:
        msg = await message.answer(text, parse_mode="Markdown")
        await bot.pin_chat_message(cid, msg.message_id)
    except: pass

@dp.message(Command("mute"))
async def mute_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    if not message.reply_to_message: return await message.reply("⚠️ Ответь на сообщение!")
    
    args = command.args.split(maxsplit=1) if command.args else []
    t_arg = args[0] if len(args) > 0 else "1h"
    reason = args[1] if len(args) > 1 else "Не указана"
    
    dur = parse_time(t_arg)
    if not dur: return await message.reply("⚠️ Ошибка. Пример: /mute 10m")
    
    # Лимиты 30с - 365д
    sec = dur.
