import os
import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

# Логирование
logging.basicConfig(level=logging.INFO)

# Токен из Railway Variables
TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КОНФИГУРАЦИЯ ---
# Твои ID уже здесь
ADMIN_IDS = [5349346619, 5919988510, 5569374433]

warns = {}
chat_members = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS

def parse_time(time_str: str, min_s=1):
    if not time_str: return timedelta(hours=1)
    unit = time_str[-1].lower()
    try:
        value = int(time_str[:-1])
        if unit == 's': res = timedelta(seconds=value)
        elif unit == 'm': res = timedelta(minutes=value)
        elif unit == 'h': res = timedelta(hours=value)
        elif unit == 'd': res = timedelta(days=value)
        else: res = timedelta(hours=1)
        return max(timedelta(seconds=min_s), min(res, timedelta(days=365)))
    except: return timedelta(hours=1)

# --- КНОПКИ МЕНЮ ---
def main_help_kb():
    buttons = [
        [InlineKeyboardButton(text="🛡 Модерация", callback_query_data="h_mod")],
        [InlineKeyboardButton(text="🪖 Старший Состав", callback_query_data="h_team")],
        [InlineKeyboardButton(text="🎮 Разное", callback_query_data="h_other")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "⚔️ **ШТАБ IRON EMPIRE**\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "Управление кланом и модерация.\n"
        "Выбери нужный раздел:",
        reply_markup=main_help_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("h_"))
async def help_callback(call: CallbackQuery):
    section = call.data.split("_")[1]
    back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_query_data="h_main")]])
    
    if section == "main":
        await call.message.edit_text("⚔️ **ШТАБ IRON EMPIRE**\n\nВыбери раздел:", reply_markup=main_help_kb())
    elif section == "mod":
        text = (
            "🛡 **МОДЕРАЦИЯ (ОТВЕТОМ):**\n\n"
            "🚫 `/mute [время] [причина]` — (30с - 365д)\n"
            "🔊 `/unmute` — снять мут\n"
            "⚠️ `/warn [причина]` — выдать пред\n"
            "✅ `/unwarn` — снять пред\n"
            "💀 `/ban [время] [причина]` — (1с - 365д)\n"
            "🔓 `/unban [ID]` — разбанить по ID"
        )
        await call.message.edit_text(text, reply_markup=back, parse_mode="Markdown")
    elif section == "team":
        text = (
            "🪖 **СТАРШИЙ СОСТАВ:**\n\n"
            "👑 **Никита** — Лидер\n"
            "🎖 **Арлан** — Гл. Заместитель\n"
            "🥈 **Ярик** — Заместитель\n"
            "🥈 **Вакансия** — Заместитель\n"
            "🥈 **Вакансия** — Заместитель\n"
            "💻 **Олег** — Тех. Админ"
        )
        await call.message.edit_text(text, reply_markup=back, parse_mode="Markdown")
    elif section == "other":
        text = "🎮 **РАЗНОЕ:**\n\n🍺 `/beer` — пиво\n🚩 `/army` — сбор состава (пин)"
        await call.message.edit_text(text, reply_markup=back, parse_mode="Markdown")
    await call.answer()

# --- ЛОГИКА МОДЕРАЦИИ ---

@dp.message(Command("mute"))
async def mute_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    args = command.args.split(maxsplit=1) if command.args else []
    t_val = args[0] if len(args) > 0 else "1h"
    reason = args[1] if len(args) > 1 else "Не указана"
    until = datetime.now() + parse_time(t_val, min_s=30)
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer(f"🤐 **МУТ**\n👤 {message.reply_to_message.from_user.first_name}\n⏰ {t_val}\n📝 {reason}")
    except: await message.answer("❌ Нет прав.")

@dp.message(Command("unmute"))
async def unmute_handler(message: Message):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
        await message.answer("🔊 Мут снят.")
    except: pass

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
            until = datetime.now() + parse_time(t_val, min_s=1)
            await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id, until_date=until)
            await message.answer(f"💀 **БАН**\n👤 {message.reply_to_message.from_user.first_name}\n⏰ {t_val}\n📝 {reason}")
    except: pass

@dp.message(Command("unban"))
async def unban_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not command.args: return
    try:
        await bot.unban_chat_member(message.chat.id, int(command.args), only_if_banned=True)
        await message.answer(f"🔓 Пользователь {command.args} разбанен.")
    except: pass

@dp.message(Command("warn"))
async def warn_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    reason = command.args if command.args else "Не указана"
    warns[uid] = warns.get(uid, 0) + 1
    if warns[uid] >= 3:
        await bot.ban_chat_member(message.chat.id, uid)
        await message.answer(f"🔴 **БАН (3/3 ВАРНА)**\n👤 {message.reply_to_message.from_user.first_name}")
        warns[uid] = 0
    else:
        await message.answer(f"⚠️ **ВАРН ({warns[uid]}/3)**\n👤 {message.reply_to_message.from_user.first_name}\n📝 {reason}")

@dp.message(Command("unwarn"))
async def unwarn_handler(message: Message):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    warns[uid] = max(0, warns.get(uid, 0) - 1)
    await message.answer(f"✅ Варн снят. Всего: {warns[uid]}/3")

# --- ВСПОМОГАТЕЛЬНОЕ ---

@dp.message(Command("beer"))
async def beer_cmd(message: Message):
    liters = round(random.uniform(0.5, 5.0), 1)
    await message.answer(f"🍺 {message.from_user.first_name} жахнул {liters}л пива!")

@dp.message(Command("army"))
async def army_handler(message: Message):
    if not is_admin(message.from_user.id): return
    cid = message.chat.id
    if cid in chat_members:
        mentions = [f"[🎖](tg://user?id={u})" for u in list(chat_members[cid])[:50]]
        msg = await message.answer(f"🚨 **СБОР IRON EMPIRE!**\n\n{' '.join(mentions)}", parse_mode="Markdown")
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
