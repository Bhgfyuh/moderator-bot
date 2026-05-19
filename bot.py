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
help_cooldown = {}
chat_members = {}

# Статистика пива {user_id: {"name": name, "total": 0.0}}
beer_stats = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS and user_id not in demoted_admins

@dp.message(F.chat.type.in_({"group", "supergroup"}), ~F.text.startswith('/'))
async def collect_members(message: Message):
    cid = message.chat.id
    if cid not in chat_members: chat_members[cid] = set()
    chat_members[cid].add(message.from_user.id)

# --- МИНИ-ИГРА: ПИВО ---
@dp.message(Command("beer"))
async def beer_game(message: Message):
    user_name = message.from_user.first_name
    uid = message.from_user.id
    
    # Шанс 5% на 5 литров
    if random.random() < 0.05:
        liters = 5.0
    else:
        liters = round(random.uniform(0.5, 4.9), 1)

    # Записываем в статистику
    if uid not in beer_stats:
        beer_stats[uid] = {"name": user_name, "total": 0.0}
    beer_stats[uid]["total"] = round(beer_stats[uid]["total"] + liters, 1)
    beer_stats[uid]["name"] = user_name # Обновляем имя, если сменил

    if liters == 5.0:
        try:
            until = datetime.now() + timedelta(minutes=30)
            await bot.restrict_chat_member(message.chat.id, uid, ChatPermissions(can_send_messages=False), until_date=until)
            await message.answer(f"🍺 {user_name} выпил **5.0 л.**!\n😵 Он так сильно напился, что упал под стол (мут 30 мин).")
        except:
            await message.answer(f"🍺 {user_name} выпил **5.0 л.**! Но мут выдать не удалось.")
    else:
        await message.answer(f"🍺 {user_name}, твоя порция: **{liters} л.**\n📈 Всего выпито: {beer_stats[uid]['total']} л.")

# --- ТОП ПИВОМАНОВ ---
@dp.message(Command("beer_top"))
async def beer_top(message: Message):
    if not beer_stats:
        return await message.answer("🍺 В баре пока пусто. Никто еще не пил!")

    # Сортируем по количеству литров (от большего к меньшему)
    sorted_top = sorted(beer_stats.values(), key=lambda x: x['total'], reverse=True)
    top_5 = sorted_top[:5]

    text = "🏆 **ТОП-5 ПИВОМАНОВ ГРУППЫ** 🏆\n"
    text += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
    
    medals = ["🥇", "🥈", "🥉", "🍺", "🍺"]
    for i, user in enumerate(top_5):
        text += f"{medals[i]} **{user['name']}** — {user['total']} л.\n"
    
    text += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
    text += "Хочешь в топ? Пиши /beer!"
    
    await message.answer(text, parse_mode="Markdown")

# --- ХЕЛП ---
@dp.message(Command("help"))
async def help_handler(message: Message):
    text = (
        "📜 **КОМАНДЫ:**\n\n"
        "🎮 **Игры:**\n"
        "🔹 `/beer` — Выпить пива\n"
        "🔹 `/beer_top` — Рейтинг алкоголиков\n\n"
        "🛡 **Модерация:**\n"
        "🔹 `/mute` / `/unmute` / `/warn` / `/ban` / `/army` \n\n"
        "🛡 **СОСТАВ:** Никита, Олег, Арлан, Ярик"
    )
    await message.answer(text, parse_mode="Markdown")

# --- ОСТАЛЬНЫЕ ФУНКЦИИ (MUTE, ARMY И Т.Д.) ---
# [Оставь их из предыдущего стабильного кода]

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
