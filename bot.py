import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

OWNER_ID = 5349346619
ADMIN_IDS = [5349346619, 5919988510, 5569374433]
demoted_admins = set()

# База данных пользователей (кто хоть раз писал при боте)
chat_members = {} # {chat_id: {user_id1, user_id2}}

warns = {}
help_cooldown = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS and user_id not in demoted_admins

# Сборщик ID пользователей (запоминает всех, кто пишет)
@dp.message(F.text, ~F.text.startswith('/'))
async def collect_members(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if chat_id not in chat_members:
        chat_members[chat_id] = set()
    
    chat_members[chat_id].add(user_id)

# --- ОБНОВЛЕННАЯ КОМАНДА: ARMY ---
@dp.message(Command("army"))
async def army_call(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    
    chat_id = message.chat.id
    if chat_id not in chat_members or not chat_members[chat_id]:
        return await message.answer("📝 В моей базе пока нет участников. Пусть все что-нибудь напишут!")

    reason = command.args if command.args else "Срочное построение!"
    
    # Формируем список упоминаний через эмодзи
    mentions = []
    emojis = ["🎖", "🪖", "🔫", "🛡", "🔥", "🚩", "🚨"]
    
    for i, user_id in enumerate(chat_members[chat_id]):
        emoji = emojis[i % len(emojis)]
        # Скрытое упоминание: [эмодзи](tg://user?id=ID)
        mentions.append(f"[{emoji}](tg://user?id={user_id})")
    
    # Разбиваем на части, если участников очень много (ТГ лимит 4096 символов)
    mentions_str = " ".join(mentions)
    
    army_text = (
        "🚨 **ВОЕННЫЕ СБОРЫ ОБЪЯВЛЕНЫ!** 🚨\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"📢 **ПРИКАЗ:** {reason}\n\n"
        f"👥 **СОСТАВ К ПРИЗЫВУ:**\n{mentions_str}\n\n"
        "⚡️ Явка 100%! Живо!"
    )
    
    msg = await message.answer(army_text, parse_mode="Markdown")
    try:
        await bot.pin_chat_message(chat_id, msg.message_id)
    except:
        pass

# --- ОСТАЛЬНЫЕ КОМАНДЫ (БЕЗ ИЗМЕНЕНИЙ) ---
# ... (mute, warn, ban, demote — оставляй из прошлого кода) ...
