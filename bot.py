import os
import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

# Логирование для отслеживания ошибок
logging.basicConfig(level=logging.INFO)

# Берем токен из секретов Railway
TOKEN = os.getenv('BOT_TOKEN') 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- БАЗА ДАННЫХ (в памяти) ---
ADMIN_IDS = [5349346619, 5919988510, 5569374433]
warns = {}
chat_members = {}
beer_stats = {}
beer_cooldown = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS

def parse_time(time_str: str):
    if not time_str: return timedelta(hours=1)
    unit = time_str[-1].lower()
    try:
        value = int(time_str[:-1])
        if unit == 's': res = timedelta(seconds=value)
        elif unit == 'm': res = timedelta(minutes=value)
        elif unit == 'h': res = timedelta(hours=value)
        elif unit == 'd': res = timedelta(days=value)
        else: res = timedelta(hours=1)
        
        if res < timedelta(seconds=30): return timedelta(seconds=30)
        if res > timedelta(days=365): return timedelta(days=365)
        return res
    except: return timedelta(hours=1)

# --- КЛАВИАТУРЫ ---
def get_help_kb():
    buttons = [
        [InlineKeyboardButton(text="🎮 Развлечения", callback_query_data="help_fun"),
         InlineKeyboardButton(text="🛡 Модерация", callback_query_data="help_mod")],
        [InlineKeyboardButton(text="📢 Управление", callback_query_data="help_admin"),
         InlineKeyboardButton(text="🪖 Состав", callback_query_data="help_team")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- КОМАНДЫ ---

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "⚔️ **ЦЕНТРАЛЬНЫЙ ШТАБ IRON EMPIRE**\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "Добро пожаловать в систему управления кланом.\n"
        "Выбери нужный раздел ниже:",
        reply_markup=get_help_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("help_"))
async def help_callback(call: CallbackQuery):
    section = call.data.split("_")[1]
    back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_query_data="help_main")]])
    
    texts = {
        "fun": "🎮 **РАЗВЛЕЧЕНИЯ**\n\n🍺 `/beer` — выпить пива (КД 5ч)\n🏆 `/beer_top` — рейтинг топ-алкашей",
        "mod": "🛡 **МОДЕРАЦИЯ (ОТВЕТОМ)**\n\n🚫 `/mute [время] [причина]` (от 30с до 365д)\n🔊 `/unmute` — размут\n⚠️ `/warn [причина]` — пред (3/3=💀)\n✅ `/unwarn` — снять пред\n💀 `/ban [причина]` — бан навсегда",
        "admin": "📢 **УПРАВЛЕНИЕ**\n\n🚩 `/army` — общий сбор клана (пин всех)",
        "team": "🪖 **СТАРШИЙ СОСТАВ**\n\n👑 Лидер: **Никита**\n🎖 Замы: **Арлан**, **Ярик**\n💻 Тех: **Олег**"
    }
    
    if section == "main":
        await call.message.edit_text("⚔️ **ЦЕНТРАЛЬНЫЙ ШТАБ IRON EMPIRE**\n\nВыбери раздел:", reply_markup=get_help_kb())
    else:
        await call.message.edit_text(texts.get(section, "Ошибка"), reply_markup=back_kb, parse_mode="Markdown")
    await call.answer()

# --- МОДЕРАЦИЯ ---

@dp.message(Command("mute"))
async def mute_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    args = command.args.split(maxsplit=1) if command.args else []
    t_val = args[0] if len(args) > 0 else "1h"
    reason = args[1] if len(args) > 1 else "Не указана"
    until = datetime.now() + parse_time(t_val)
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer(f"🤐 **Мут!**\n👤 {message.reply_to_message.from_user.first_name}\n⏰ Срок: {t_val}\n📝 Причина: {reason}")
    except: await message.answer("❌ Нет прав администратора у бота!")

@dp.message(Command("unmute"))
async def unmute_handler(message: Message):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
        await message.answer("🔊 Голос возвращен!")
    except: pass

@dp.message(Command("warn"))
async def warn_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    reason = command.args if command.args else "Не указана"
    warns[uid] = warns.get(uid, 0) + 1
    if warns[uid] >= 3:
        await bot.ban_chat_member(message.chat.id, uid)
        await message.answer(f"🔴 **БАН (3/3 варна)!**\n👤 {message.reply_to_message.from_user.first_name}")
        warns[uid] = 0
    else:
        await message.answer(f"⚠️ **ВАРН ({warns[uid]}/3)**\n👤 {message.reply_to_message.from_user.first_name}\n📝 Причина: {reason}")

@dp.message(Command("unwarn"))
async def unwarn_handler(message: Message):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    warns[uid] = max(0, warns.get(uid, 0) - 1)
    await message.answer(f"✅ **Варн снят!** Счет: {warns[uid]}/3")

@dp.message(Command("ban"))
async def ban_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    reason = command.args if command.args else "Не указана"
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"💀 **БАН**\n👤 {message.reply_to_message.from_user.first_name}\n📝 Причина: {reason}")
    except: pass

# --- ПИВО ---

@dp.message(Command("beer"))
async def beer_game(message: Message):
    uid = message.from_user.id
    now = datetime.now()
    if uid in beer_cooldown and (now - beer_cooldown[uid]) < timedelta(hours=5):
        rem = timedelta(hours=5) - (now - beer_cooldown[uid])
        return await message.answer(f"🚫 Рано! Жди еще {int(rem.total_seconds()//3600)}ч.")
    liters = 5.0 if random.random() < 0.05 else round(random.uniform(0.5, 4.9), 1)
    if uid not in beer_stats: beer_stats[uid] = {"name": message.from_user.first_name, "total": 0.0}
    beer_stats[uid]["total"] = round(beer_stats[uid]["total"] + liters, 1)
    beer_cooldown[uid] = now
    await message.answer(f"🍺 {message.from_user.first_name}: {liters} л. (Всего: {beer_stats[uid]['total']} л.)")

@dp.message(Command("beer_top"))
async def beer_top_cmd(message: Message):
    if not beer_stats: return await message.answer("🍺 Пусто.")
    top = sorted(beer_stats.values(), key=lambda x: x['total'], reverse=True)[:5]
    res = "🏆 **ТОП ЛЮБИТЕЛЕЙ ПИВА:**\n" + "\n".join([f"• {u['name']}: {u['total']} л." for u in top])
    await message.answer(res)

# --- АРМИЯ ---

@dp.message(Command("army"))
async def army_handler(message: Message):
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
