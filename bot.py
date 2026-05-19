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

# Токен из переменных окружения Railway
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

def parse_time(time_str: str):
    if not time_str: return timedelta(hours=1)
    unit = time_str[-1].lower()
    try:
        value = int(time_str[:-1])
        if unit == 'm': return timedelta(minutes=value)
        if unit == 'h': return timedelta(hours=value)
        if unit == 'd': return timedelta(days=value)
    except: return None
    return timedelta(hours=1)

# --- КОМАНДЫ МОДЕРАЦИИ ---

@dp.message(Command("mute"))
async def mute_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    
    args = command.args.split(maxsplit=1) if command.args else []
    time_val = args[0] if len(args) > 0 else "1h"
    reason = args[1] if len(args) > 1 else "Не указана"
    
    duration = parse_time(time_val)
    until = datetime.now() + duration
    
    try:
        await bot.restrict_chat_member(
            message.chat.id, 
            message.reply_to_message.from_user.id, 
            ChatPermissions(can_send_messages=False), 
            until_date=until
        )
        await message.answer(f"🤐 **Мут**\n👤 Кому: {message.reply_to_message.from_user.first_name}\n⏰ Срок: {time_val}\n📝 Причина: {reason}")
    except: await message.answer("❌ Ошибка прав.")

@dp.message(Command("warn"))
async def warn_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    
    uid = message.reply_to_message.from_user.id
    reason = command.args if command.args else "Не указана"
    
    warns[uid] = warns.get(uid, 0) + 1
    
    if warns[uid] >= 3:
        try:
            await bot.ban_chat_member(message.chat.id, uid)
            await message.answer(f"🔴 **Бан** за 3/3 варна!\n👤 Нарушитель: {message.reply_to_message.from_user.first_name}")
            warns[uid] = 0
        except: pass
    else:
        await message.answer(f"⚠️ **Варн ({warns[uid]}/3)**\n👤 Кому: {message.reply_to_message.from_user.first_name}\n📝 Причина: {reason}")

@dp.message(Command("unwarn"))
async def unwarn_handler(message: Message):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    
    uid = message.reply_to_message.from_user.id
    if uid in warns and warns[uid] > 0:
        warns[uid] -= 1
        await message.answer(f"✅ **Варн снят**\n👤 Кому: {message.reply_to_message.from_user.first_name}\n📊 Осталось варнов: {warns[uid]}/3")
    else:
        await message.answer("ℹ️ У пользователя нет активных варнов.")

@dp.message(Command("ban"))
async def ban_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    
    reason = command.args if command.args else "Не указана"
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"💀 **Бан навсегда**\n👤 Кому: {message.reply_to_message.from_user.first_name}\n📝 Причина: {reason}")
    except: await message.answer("❌ Не удалось забанить.")

# --- ОСТАЛЬНЫЕ КОМАНДЫ (BEER, ARMY) ---

@dp.message(Command("help"))
async def help_handler(message: Message):
    help_text = (
        "⚔️ **ШТАБ IRON EMPIRE** ⚔️\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        "🍺 `/beer` — Выпить (КД 5ч)\n"
        "🏆 `/beer_top` — Рейтинг\n\n"
        "🚫 `/mute [время] [причина]` (ответ)\n"
        "⚠️ `/warn [причина]` — Варн (ответ)\n"
        "✅ `/unwarn` — Снять варн (ответ)\n"
        "💀 `/ban [причина]` — Бан (ответ)\n\n"
        "🚩 `/army [текст]` — Сбор состава\n\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    )
    await message.answer(help_text, parse_mode="Markdown")

# [Код /beer, /beer_top и collect_members оставь как в прошлом варианте]
# --- ПИВО ---
@dp.message(Command("beer"))
async def beer_game(message: Message):
    uid = message.from_user.id
    now = datetime.now()
    if uid in beer_cooldown and (now - beer_cooldown[uid]) < timedelta(hours=5):
        rem = timedelta(hours=5) - (now - beer_cooldown[uid])
        h, m = int(rem.total_seconds() // 3600), int((rem.total_seconds() % 3600) // 60)
        return await message.answer(f"🚫 Рано! Жди еще {h}ч. {m}м.")
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

@dp.message(Command("army"))
async def army_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    cid = message.chat.id
    if cid not in chat_members or not chat_members[cid]: return
    mentions = [f"[🎖](tg://user?id={u})" for u in list(chat_members[cid])[:50]]
    msg = await message.answer(f"🚨 **ОБЩИЙ СБОР!**\n\n{' '.join(mentions)}", parse_mode="Markdown")
    try: await bot.pin_chat_message(cid, msg.message_id)
    except: pass

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
