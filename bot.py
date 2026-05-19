import os
import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

# Логирование
logging.basicConfig(level=logging.INFO)

# ПОЛУЧАЕМ СКРЫТЫЙ ТОКЕН ИЗ НАСТРОЕК RAILWAY
TOKEN = os.getenv('BOT_TOKEN') 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КОНФИГУРАЦИЯ ---
OWNER_ID = 5349346619
ADMIN_IDS = [5349346619, 5919988510, 5569374433]
demoted_admins = set()
warns = {}
chat_members = {}
beer_stats = {}
beer_cooldown = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS and user_id not in demoted_admins

# --- КОМАНДЫ МОДЕРАЦИИ (ОТВЕТОМ НА СООБЩЕНИЕ) ---

@dp.message(Command("help"))
async def help_handler(message: Message):
    help_text = (
        "⚔️ **ШТАБ IRON EMPIRE** ⚔️\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        "🍺 `/beer` — Выпить (КД 5ч)\n"
        "🏆 `/beer_top` — Рейтинг\n\n"
        "🚫 `/mute [время]` — Мут (ответ)\n"
        "⚠️ `/warn` — Варн (3/3 = бан)\n"
        "💀 `/ban` — Бан (ответ)\n\n"
        "🚩 `/army [текст]` — Сбор состава\n\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "🪖 **СОСТАВ:** Никита, Олег, Арлан, Ярик"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("beer"))
async def beer_game(message: Message):
    uid = message.from_user.id
    now = datetime.now()
    
    if uid in beer_cooldown and (now - beer_cooldown[uid]) < timedelta(hours=5):
        rem = timedelta(hours=5) - (now - beer_cooldown[uid])
        h, m = int(rem.total_seconds() // 3600), int((rem.total_seconds() % 3600) // 60)
        return await message.answer(f"🚫 Жди еще {h}ч. {m}м.")
    
    liters = 5.0 if random.random() < 0.05 else round(random.uniform(0.5, 4.9), 1)
    if uid not in beer_stats: beer_stats[uid] = {"name": message.from_user.first_name, "total": 0.0}
    beer_stats[uid]["total"] = round(beer_stats[uid]["total"] + liters, 1)
    beer_cooldown[uid] = now

    if liters == 5.0:
        try:
            await bot.restrict_chat_member(message.chat.id, uid, ChatPermissions(can_send_messages=False), until_date=now + timedelta(minutes=30))
            await message.answer(f"🍺 **{message.from_user.first_name}** выпил 5.0 л. и отключился на 30 мин!")
        except: await message.answer(f"🍺 **{message.from_user.first_name}** выпил 5.0 л.!")
    else:
        await message.answer(f"🍺 {message.from_user.first_name}: {liters} л. (Всего: {beer_stats[uid]['total']} л.)")

@dp.message(Command("beer_top"))
async def beer_top_cmd(message: Message):
    if not beer_stats: return await message.answer("🍺 В баре пусто.")
    top = sorted(beer_stats.values(), key=lambda x: x['total'], reverse=True)[:5]
    res = "🏆 **ТОП ПИВОМАНОВ:**\n" + "\n".join([f"• {u['name']}: {u['total']} л." for u in top])
    await message.answer(res)

@dp.message(Command("mute"))
async def mute_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    try:
        until = datetime.now() + timedelta(hours=1)
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer(f"🤐 Мут выдан.")
    except: await message.answer("❌ Нет прав.")

@dp.message(Command("army"))
async def army_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    cid = message.chat.id
    if cid not in chat_members or not chat_members[cid]: return
    mentions = [f"[🎖](tg://user?id={u})" for u in list(chat_members[cid])[:50]]
    msg = await message.answer(f"🚨 **ОБЩИЙ СБОР!**\n\n{' '.join(mentions)}", parse_mode="Markdown")
    try: await bot.pin_chat_message(cid, msg.message_id)
    except: pass

# --- СБОР ID УЧАСТНИКОВ (В КОНЦЕ) ---
@dp.message(F.chat.type.in_({"group", "supergroup"}), ~F.text.startswith('/'))
async def collect_members(message: Message):
    cid = message.chat.id
    if cid not in chat_members: chat_members[cid] = set()
    chat_members[cid].add(message.from_user.id)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
