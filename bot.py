import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)

TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КОНФИГУРАЦИЯ ---
OWNER_ID = 5349346619
ADMIN_IDS = [5349346619, 5919988510, 5569374433]
demoted_admins = set()
warns = {}
chat_members = {}

# Статистика и Кулдауны
beer_stats = {} # {user_id: {"name": str, "total": float}}
beer_cooldown = {} # {user_id: datetime}

def is_admin(user_id):
    return user_id in ADMIN_IDS and user_id not in demoted_admins

@dp.message(F.chat.type.in_({"group", "supergroup"}), ~F.text.startswith('/'))
async def collect_members(message: Message):
    cid = message.chat.id
    if cid not in chat_members: chat_members[cid] = set()
    chat_members[cid].add(message.from_user.id)

# --- МИНИ-ИГРА: ПИВО С КД 5 ЧАСОВ ---
@dp.message(Command("beer"))
async def beer_game(message: Message):
    uid = message.from_user.id
    user_name = message.from_user.first_name
    now = datetime.now()

    # Проверка КД (5 часов)
    if uid in beer_cooldown:
        last_time = beer_cooldown[uid]
        diff = now - last_time
        if diff < timedelta(hours=5):
            remaining = timedelta(hours=5) - diff
            hours_rem = int(remaining.total_seconds() // 3600)
            mins_rem = int((remaining.total_seconds() % 3600) // 60)
            return await message.answer(
                f"🚫 **Рано за добавкой!**\n"
                f"Твой организм еще не переработал прошлую порцию.\n"
                f"Заходи через: **{hours_rem}ч. {mins_rem}мин.**"
            )

    # Логика выпадения
    if random.random() < 0.05:
        liters = 5.0
    else:
        liters = round(random.uniform(0.5, 4.9), 1)

    # Обновление статистики
    if uid not in beer_stats:
        beer_stats[uid] = {"name": user_name, "total": 0.0}
    beer_stats[uid]["total"] = round(beer_stats[uid]["total"] + liters, 1)
    beer_stats[uid]["name"] = user_name
    
    # Устанавливаем новое время КД
    beer_cooldown[uid] = now

    if liters == 5.0:
        try:
            until = now + timedelta(minutes=30)
            await bot.restrict_chat_member(message.chat.id, uid, ChatPermissions(can_send_messages=False), until_date=until)
            await message.answer(f"🍺 {user_name} жадно выпил **5.0 л.**!\n😵 Участник в хлам, он не может говорить 30 минут.")
        except:
            await message.answer(f"🍺 {user_name} выпил **5.0 л.**! (Мут не удался)")
    else:
        await message.answer(
            f"🍺 {user_name}, держи свои **{liters} л.**\n"
            f"📈 Всего в тебе: {beer_stats[uid]['total']} л.\n"
            f"🕒 Следующая кружка через 5 часов."
        )

# --- ТОП ПИВОМАНОВ ---
@dp.message(Command("beer_top"))
async def beer_top(message: Message):
    if not beer_stats:
        return await message.answer("🍺 В баре пусто.")
    sorted_top = sorted(beer_stats.values(), key=lambda x: x['total'], reverse=True)[:5]
    text = "🏆 **ТОП-5 ПИВОМАНОВ** 🏆\n"
    medals = ["🥇", "🥈", "🥉", "🍺", "🍺"]
    for i, user in enumerate(sorted_top):
        text += f"{medals[i]} **{user['name']}** — {user['total']} л.\n"
    await message.answer(text, parse_mode="Markdown")

# --- КОМАНДА /ARMY ---
@dp.message(Command("army"))
async def army_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    cid = message.chat.id
    if cid not in chat_members or not chat_members[cid]:
        return await message.answer("📝 База пуста.")
    reason = command.args if command.args else "Срочный сбор!"
    emojis = ["🎖","🪖","🔫","🛡"]
    mentions = [f"[{emojis[i % 4]}](tg://user?id={uid})" for i, uid in enumerate(list(chat_members[cid])[:50])]
    msg = await message.answer(f"🚨 **СБОР!**\nПриказ: {reason}\n\n{' '.join(mentions)}", parse_mode="Markdown")
    try: await bot.pin_chat_message(cid, msg.message_id)
    except: pass

# --- ОСТАЛЬНЫЕ КОМАНДЫ (MUTE, WARN, HELP) ---
# ... (Оставь как было в прошлом стабильном коде) ...

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
