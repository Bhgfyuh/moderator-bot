import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

# Настройка логов
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
beer_stats = {}
beer_cooldown = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS and user_id not in demoted_admins

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

# Сборщик участников для /army
@dp.message(F.chat.type.in_({"group", "supergroup"}), ~F.text.startswith('/'))
async def collect_members(message: Message):
    cid = message.chat.id
    if cid not in chat_members: chat_members[cid] = set()
    chat_members[cid].add(message.from_user.id)

# --- КРАСИВЫЙ ХЕЛП ---
@dp.message(Command("help"))
async def help_handler(message: Message):
    uid = message.from_user.id
    
    # Анти-спам для обычных игроков
    if not is_admin(uid):
        now = datetime.now()
        last = help_cooldown.get(uid)
        if last and (now - last).total_seconds() < 300:
            try:
                await bot.restrict_chat_member(message.chat.id, uid, ChatPermissions(can_send_messages=False), until_date=now + timedelta(minutes=20))
                return await message.answer("🤫 Не спамь командой /help. Отдохни в муте 20 минут.")
            except: return
        help_cooldown[uid] = now

    help_text = (
        "⚔️ **ЦЕНТРАЛЬНЫЙ ШТАБ УПРАВЛЕНИЯ** ⚔️\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        "🎮 **РАЗВЛЕЧЕНИЯ:**\n"
        "🍺 `/beer` — Опрокинуть бокал (КД 5ч)\n"
        "🏆 `/beer_top` — Список главных пивоманов\n\n"
        "🛡 **МОДЕРАЦИЯ (ОТВЕТОМ):**\n"
        "🚫 `/mute [время] [причина]` — Заткнуть\n"
        "🔊 `/unmute` — Вернуть голос\n"
        "⚠️ `/warn [причина]` — Выдать пред (3/3 = ❌)\n"
        "✅ `/unwarn` — Снять один пред\n"
        "💀 `/ban [причина]` — Выгнать навсегда\n\n"
        "📢 **ОБЩИЕ КОМАНДЫ:**\n"
        "🚩 `/army [текст]` — Массовый сбор (пин)\n\n"
        "👑 **ДЛЯ ЛИДЕРА:**\n"
        "❌ `/demote` | ✅ `/promote` — Упр. админами\n\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "🪖 **СТАРШИЙ СОСТАВ:**\n"
        "• 👑 Лидер: **Никита**\n"
        "• 💻 Тех. Админ: **Олег**\n"
        "• 🎖 Гл. Зам: **Арлан**\n"
        "• 🥈 Зам: **Ярик**\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    )
    await message.answer(help_text, parse_mode="Markdown")

# --- ПИВО ---
@dp.message(Command("beer"))
async def beer_game(message: Message):
    uid = message.from_user.id
    now = datetime.now()
    if uid in beer_cooldown and (now - beer_cooldown[uid]) < timedelta(hours=5):
        rem = timedelta(hours=5) - (now - beer_cooldown[uid])
        return await message.answer(f"🚫 Рано! Жди еще **{int(rem.total_seconds()//3600)}ч. {int((rem.total_seconds()%3600)//60)}м.**")
    
    liters = 5.0 if random.random() < 0.05 else round(random.uniform(0.5, 4.9), 1)
    if uid not in beer_stats: beer_stats[uid] = {"name": message.from_user.first_name, "total": 0.0}
    beer_stats[uid]["total"] = round(beer_stats[uid]["total"] + liters, 1)
    beer_cooldown[uid] = now

    if liters == 5.0:
        try:
            await bot.restrict_chat_member(message.chat.id, uid, ChatPermissions(can_send_messages=False), until_date=now + timedelta(minutes=30))
            await message.answer(f"🍺 **{message.from_user.first_name}** выпил 5.0 л. и вырубился на 30 мин!")
        except: await message.answer(f"🍺 **{message.from_user.first_name}** выпил 5.0 л.!")
    else:
        await message.answer(f"🍺 **{message.from_user.first_name}**, твоя порция: {
