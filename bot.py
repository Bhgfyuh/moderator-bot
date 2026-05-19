import os
import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пытаемся взять токен
TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    logger.error("ОШИБКА: Токен не найден в переменных Railway (BOT_TOKEN)!")
else:
    logger.info("Токен успешно подгружен.")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ТВОИ НАСТРОЙКИ ---
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
        return max(timedelta(seconds=30), min(res, timedelta(days=366)))
    except: return timedelta(hours=1)

# --- МЕНЮ HELP С КНОПКАМИ ---
def get_help_kb():
    buttons = [
        [InlineKeyboardButton(text="🎮 Развлечения", callback_query_data="help_fun"),
         InlineKeyboardButton(text="🛡 Модерация", callback_query_data="help_mod")],
        [InlineKeyboardButton(text="📢 Управление", callback_query_data="help_admin"),
         InlineKeyboardButton(text="🪖 Состав", callback_query_data="help_team")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "⚔️ **ЦЕНТРАЛЬНЫЙ ШТАБ IRON EMPIRE**\n\nВыбери раздел управления:",
        reply_markup=get_help_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("help_"))
async def help_callback(call: CallbackQuery):
    section = call.data.split("_")[1]
    back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_query_data="help_main")]])
    texts = {
        "fun": "🎮 **РАЗВЛЕЧЕНИЯ**\n\n🍺 `/beer` — выпить пива (КД 5ч)\n🏆 `/beer_top` — топ",
        "mod": "🛡 **МОДЕРАЦИЯ**\n\n🚫 `/mute [время] [причина]`\n⚠️ `/warn [причина]` — пред\n✅ `/unwarn` — снять пред\n💀 `/ban [время/0] [причина]` (0 - навсегда)",
        "admin": "📢 **УПРАВЛЕНИЕ**\n\n🚩 `/army` — общий сбор (пин)",
        "team": "🪖 **СТАРШИЙ СОСТАВ**\n\n👑 Лидер: **Никита**\n🎖 Замы: **Арлан, Ярик, Олег**"
    }
    if section == "main":
        await call.message.edit_text("⚔️ **ЦЕНТРАЛЬНЫЙ ШТАБ IRON EMPIRE**", reply_markup=get_help_kb())
    else:
        await call.message.edit_text(texts.get(section, "Ошибка"), reply_markup=back_kb, parse_mode="Markdown")
    await call.answer()

# --- КОМАНДЫ (БАН, МУТ, ВАРН) ---
@dp.message(Command("ban"))
async def ban_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    args = command.args.split(maxsplit=1) if command.args else []
    t_val = args[0] if len(args) > 0 else "0"
    reason = args[1] if len(args) > 1 else "Не указана"
    try:
        if t_val == "0":
            await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            await message.answer(f"💀 **БАН НАВСЕГДА**\n👤 {message.reply_to_message.from_user.first_name}\n📝 {reason}")
        else:
            until = datetime.now() + parse_time(t_val)
            await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id, until_date=until)
            await message.answer(f"💀 **БАН**\n👤 {message.reply_to_message.from_user.first_name}\n⏰ Срок: {t_val}\n📝 {reason}")
    except Exception as e: await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("mute"))
async def mute_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    args = command.args.split(maxsplit=1) if command.args else []
    t_val = args[0] if len(args) > 0 else "1h"
    reason = args[1] if len(args) > 1 else "Не указана"
    until = datetime.now() + parse_time(t_val)
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer(f"🤐 **МУТ**\n👤 {message.reply_to_message.from_user.first_name}\n⏰ Срок: {t_val}\n📝 {reason}")
    except Exception as e: await message.answer(f"❌ Ошибка: {e}")

# --- ВСПОМОГАТЕЛЬНОЕ ---
@dp.message(Command("beer"))
async def beer_cmd(message: Message):
    uid = message.from_user.id
    now = datetime.now()
    if uid in beer_cooldown and (now - beer_cooldown[uid]) < timedelta(hours=5):
        return await message.answer("🚫 Жди 5 часов.")
    liters = round(random.uniform(0.5, 5.0), 1)
    beer_stats[uid] = beer_stats.get(uid, 0) + liters
    beer_cooldown[uid] = now
    await message.answer(f"🍺 {message.from_user.first_name} выпил {liters} л. (Всего: {beer_stats[uid]} л.)")

@dp.message(Command("army"))
async def army_handler(message: Message):
    if not is_admin(message.from_user.id): return
    cid = message.chat.id
    if cid in chat_members:
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
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Бот упал при запуске: {e}")
