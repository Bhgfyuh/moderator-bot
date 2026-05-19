import os
import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

# Включаем логи, чтобы видеть ошибки в консоли Railway
logging.basicConfig(level=logging.INFO)

# Берем токен из Variables в Railway
TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Данные админов
ADMIN_IDS = [5349346619, 5919988510, 5569374433]
chat_members = {}
beer_stats = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS

def parse_time(time_str: str):
    unit = time_str[-1].lower() if time_str else 'h'
    try:
        value = int(time_str[:-1]) if len(time_str) > 1 else 1
        if unit == 'm': return timedelta(minutes=value)
        if unit == 'h': return timedelta(hours=value)
        if unit == 'd': return timedelta(days=value)
        return timedelta(hours=1)
    except: return timedelta(hours=1)

# --- КРАСИВЫЙ ХЕЛП ---
@dp.message(Command("help"))
async def help_handler(message: Message):
    # Создаем кнопки (например, ссылка на тебя или на канал клана)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👑 Связь с Лидером", url="tg://user?id=5349346619")],
        [InlineKeyboardButton(text="⚔️ Группа Клана", url="https://t.me/your_clan_link")] # Замени ссылку
    ])

    text = (
        "⚔️ **ШТАБ IRON EMPIRE** ⚔️\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        "🍺 **ИГРА:**\n"
        "• `/beer` — выпить пива\n"
        "• `/beer_top` — рейтинг\n\n"
        "🛡 **АДМИНКА (ОТВЕТОМ):**\n"
        "• `/mute [время]` — мут (напр. `1h`)\n"
        "• `/ban [время]` — бан (напр. `7d` или `0` - навсегда)\n"
        "• `/unmute` — снять мут\n\n"
        "📢 **УПРАВЛЕНИЕ:**\n"
        "• `/army` — сбор состава\n\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    )
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

# --- ЛОГИКА БАНА И МУТА ---
@dp.message(Command("ban"))
async def ban_cmd(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    t_val = command.args if command.args else "0"
    try:
        if t_val == "0":
            await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            await message.answer(f"💀 **Навсегда выгнан:** {message.reply_to_message.from_user.first_name}")
        else:
            until = datetime.now() + parse_time(t_val)
            await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id, until_date=until)
            await message.answer(f"💀 **Бан на {t_val}:** {message.reply_to_message.from_user.first_name}")
    except: await message.answer("❌ Нет прав.")

@dp.message(Command("mute"))
async def mute_cmd(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    t_val = command.args if command.args else "1h"
    until = datetime.now() + parse_time(t_val)
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer(f"🤐 **Мут на {t_val}:** {message.reply_to_message.from_user.first_name}")
    except: await message.answer("❌ Нет прав.")

# --- ОСТАЛЬНОЕ ---
@dp.message(Command("beer"))
async def beer_cmd(message: Message):
    liters = round(random.uniform(0.5, 5.0), 1)
    uid = message.from_user.id
    beer_stats[uid] = beer_stats.get(uid, 0) + liters
    await message.answer(f"🍺 {message.from_user.first_name} жахнул {liters}л! (Всего: {beer_stats[uid]}л)")

@dp.message(Command("army"))
async def army_cmd(message: Message):
    if not is_admin(message.from_user.id): return
    cid = message.chat.id
    if cid in chat_members:
        mentions = [f"[🎖](tg://user?id={u})" for u in list(chat_members[cid])[:50]]
        await message.answer(f"🚨 **ОБЩИЙ СБОР!**\n\n{' '.join(mentions)}", parse_mode="Markdown")

@dp.message(F.chat.type.in_({"group", "supergroup"}), ~F.text.startswith('/'))
async def collect(message: Message):
    cid = message.chat.id
    if cid not in chat_members: chat_members[cid] = set()
    chat_members[cid].add(message.from_user.id)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
