import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

# 1. Логирование (помогает видеть ошибки в консоли Railway)
logging.basicConfig(level=logging.INFO)

# 2. Твой Токен
TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 3. Глобальные переменные (База данных в оперативной памяти)
OWNER_ID = 5349346619
ADMIN_IDS = [5349346619, 5919988510, 5569374433]
demoted_admins = set()
warns = {}
help_cooldown = {}
chat_members = {}
beer_stats = {}
beer_cooldown = {}

# --- Вспомогательные функции ---

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

# --- КОМАНДЫ МОДЕРАЦИИ (Должны быть в начале) ---

@dp.message(Command("help"))
async def help_handler(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        now = datetime.now()
        last = help_cooldown.get(uid, None)
        if last and (now - last).total_seconds() < 300:
            try:
                await bot.restrict_chat_member(message.chat.id, uid, ChatPermissions(can_send_messages=False), until_date=now + timedelta(minutes=20))
                return await message.answer("🤫 Не спамь! Мут 20 мин.")
            except: return
        help_cooldown[uid] = now

    help_text = (
        "⚔️ **ЦЕНТРАЛЬНЫЙ ШТАБ** ⚔️\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        "🍺 `/beer` — Выпить (КД 5ч)\n"
        "🏆 `/beer_top` — Рейтинг\n\n"
        "🚫 `/mute [время]` — Мут (ответ)\n"
        "🔊 `/unmute` — Размут (ответ)\n"
        "⚠️ `/warn` | ✅ `/unwarn` (ответ)\n"
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
        h = int(rem.total_seconds() // 3600)
        m = int((rem.total_seconds() % 3600) // 60)
        return await message.answer(f"🚫 Жди еще {h}ч. {m}м.")
    
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
        await message.answer(f"🍺 {message.from_user.first_name}: {liters} л. (Всего: {beer_stats[uid]['total']} л.)")

@dp.message(Command("beer_top"))
async def beer_top_cmd(message: Message):
    if not beer_stats: return await message.answer("🍺 Еще никто не пил.")
    top = sorted(beer_stats.values(), key=lambda x: x['total'], reverse=True)[:5]
    res = "🏆 **ТОП ЛЮБИТЕЛЕЙ ПИВА:**\n" + "\n".join([f"• {u['name']}: {u['total']} л." for u in top])
    await message.answer(res)

@dp.message(Command("army"))
async def army_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    cid = message.chat.id
    if cid not in chat_members or not chat_members[cid]: return await message.answer("📝 База пуста.")
    mentions = [f"[{['🎖','🪖','🛡'][i%3]}](tg://user?id={u})" for i, u in enumerate(list(chat_members[cid])[:50])]
    msg = await message.answer(f"🚨 **ОБЩИЙ СБОР!**\n\n{' '.join(mentions)}", parse_mode="Markdown")
    try: await bot.pin_chat_message(cid, msg.message_id)
    except: pass

@dp.message(Command("mute"))
async def mute_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    args = command.args.split(maxsplit=1) if command.args else []
    dur = parse_time(args[0] if args else "1h")
    until = datetime.now() + (dur if dur else timedelta(hours=1))
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer(f"🤐 Мут до {until.strftime('%H:%M')}")
    except Exception as e: await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("unmute"))
async def unmute_handler(message: Message):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
        await message.answer("🔊 Размучен.")
    except: pass

@dp.message(Command("warn"))
async def warn_handler(message: Message):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    warns[uid] = warns.get(uid, 0) + 1
    if warns[uid] >= 3:
        try:
            await bot.ban_chat_member(message.chat.id, uid)
            await message.answer("🔴 Бан за 3/3 варна.")
            warns[uid] = 0
        except: pass
    else: await message.answer(f"⚠️ Варн ({warns[uid]}/3)")

@dp.message(Command("unwarn"))
async def unwarn_handler(message: Message):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    warns[uid] = max(0, warns.get(uid, 0) - 1)
    await message.answer(f"✅ Варн снят ({warns[uid]}/3)")

@dp.message(Command("ban"))
async def ban_handler(message: Message):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    try: 
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer("🔴 Бан.")
    except: pass

# --- СБОРЩИК ID (ВСЕГДА В САМОМ КОНЦЕ) ---

@dp.message(F.chat.type.in_({"group", "supergroup"}), ~F.text.startswith('/'))
async def collect_members(message: Message):
    cid = message.chat.id
    if cid not in chat_members: chat_members[cid] = set()
    chat_members[cid].add(message.from_user.id)

# --- ЗАПУСК ---

async def main():
    # Удаляем вебхуки и запускаем опрос
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
