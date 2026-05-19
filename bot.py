import os
import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv('BOT_TOKEN') 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КОНФИГУРАЦИЯ ---
ADMIN_IDS = [5349346619, 5919988510, 5569374433]
warns = {}
chat_members = {}
beer_stats = {}
beer_cooldown = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS

# --- КЛАВИАТУРЫ ---
def get_help_kb():
    buttons = [
        [InlineKeyboardButton(text="🎮 Развлечения", callback_query_data="help_fun"),
         InlineKeyboardButton(text="🛡 Модерация", callback_query_data="help_mod")],
        [InlineKeyboardButton(text="📢 Управление", callback_query_data="help_admin"),
         InlineKeyboardButton(text="🪖 Состав", callback_query_data="help_team")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ОБРАБОТЧИК КНОПОК ---
@dp.callback_query(F.data.startswith("help_"))
async def help_callback(call: CallbackQuery):
    section = call.data.split("_")[1]
    
    texts = {
        "fun": "🎮 **РАЗВЛЕЧЕНИЯ**\n\n🍺 `/beer` — выпить пива (КД 5ч)\n🏆 `/beer_top` — рейтинг топ-алкашей",
        "mod": "🛡 **МОДЕРАЦИЯ (ОТВЕТОМ)**\n\n🚫 `/mute [время] [причина]`\n🔊 `/unmute` — размут\n⚠️ `/warn [причина]` — пред (3/3=💀)\n✅ `/unwarn` — снять пред\n💀 `/ban [причина]` — бан",
        "admin": "📢 **УПРАВЛЕНИЕ**\n\n🚩 `/army` — общий сбор клана (тег всех + пин)",
        "team": "🪖 **СТАРШИЙ СОСТАВ**\n\n👑 Лидер: **Никита**\n🎖 Замы: **Арлан**, **Ярик**\n💻 Тех: **Олег**"
    }
    
    back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_query_data="help_main")]])
    
    if section == "main":
        await call.message.edit_text("⚔️ **ЦЕНТРАЛЬНЫЙ ШТАБ IRON EMPIRE**\n\nВыбери нужный раздел управления:", reply_markup=get_help_kb())
    else:
        await call.message.edit_text(texts[section], reply_markup=back_kb, parse_mode="Markdown")
    await call.answer()

# --- КОМАНДА HELP ---
@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "⚔️ **ЦЕНТРАЛЬНЫЙ ШТАБ IRON EMPIRE**\n\nВыбери нужный раздел управления ниже:",
        reply_markup=get_help_kb()
    )

# --- ОСТАЛЬНОЙ КОД (ПИВО, МУТЫ И Т.Д.) ---
# (Оставляем всю логику мутов, варнов и сбора состава из предыдущих версий)

@dp.message(Command("beer"))
async def beer_game(message: Message):
    uid = message.from_user.id
    now = datetime.now()
    if uid in beer_cooldown and (now - beer_cooldown[uid]) < timedelta(hours=5):
        rem = timedelta(hours=5) - (now - beer_cooldown[uid])
        return await message.answer(f"🚫 Рано! Жди {int(rem.total_seconds()//3600)}ч.")
    
    liters = 5.0 if random.random() < 0.05 else round(random.uniform(0.5, 4.9), 1)
    if uid not in beer_stats: beer_stats[uid] = {"name": message.from_user.first_name, "total": 0.0}
    beer_stats[uid]["total"] = round(beer_stats[uid]["total"] + liters, 1)
    beer_cooldown[uid] = now
    await message.answer(f"🍺 {message.from_user.first_name}: {liters} л. (Всего: {beer_stats[uid]['total']} л.)")

@dp.message(Command("army"))
async def army_handler(message: Message):
    if not is_admin(message.from_user.id): return
    cid = message.chat.id
    if cid not in chat_members or not chat_members[cid]: return
    mentions = [f"[🎖](tg://user?id={u})" for u in list(chat_members[cid])[:50]]
    msg = await message.answer(f"🚨 **ОБЩИЙ СБОР КЛАНА!**\n\n{' '.join(mentions)}", parse_mode="Markdown")
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
