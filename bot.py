import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()

ADMIN_IDS = [5349346619, 5919988510, 5569374433]
warns = {}
chat_members = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS

def parse_time(time_str: str, min_s=1):
    if not time_str: return timedelta(hours=1)
    unit = time_str[-1].lower()
    try:
        val = int(time_str[:-1])
        if unit == 's': res = timedelta(seconds=val)
        elif unit == 'm': res = timedelta(minutes=val)
        elif unit == 'h': res = timedelta(hours=val)
        elif unit == 'd': res = timedelta(days=val)
        else: res = timedelta(hours=1)
        return max(timedelta(seconds=min_s), min(res, timedelta(days=365)))
    except: return timedelta(hours=1)

# ИСПРАВЛЕННЫЕ КНОПКИ
def get_kb():
    buttons = [
        [InlineKeyboardButton(text="🛡 Модерация", callback_query_data="h_mod")],
        [InlineKeyboardButton(text="🪖 Старший Состав", callback_query_data="h_team")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("help"))
async def help_cmd(message: Message):
    # Используем answer вместо reply для надежности
    await message.answer(
        "⚔️ **ШТАБ IRON EMPIRE**\nВыберите раздел управления:",
        reply_markup=get_kb(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("h_"))
async def help_cb(call: CallbackQuery):
    s = call.data.split("_")[1]
    back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_query_data="h_main")]])
    
    if s == "main":
        await call.message.edit_text("⚔️ **ШТАБ IRON EMPIRE**", reply_markup=get_kb())
    elif s == "mod":
        await call.message.edit_text(
            "🛡 **МОДЕРАЦИЯ:**\n\n/mute, /ban, /warn, /army", 
            reply_markup=back_kb
        )
    elif s == "team":
        await call.message.edit_text(
            "🪖 **СОСТАВ:**\nНикита, Арлан, Ярик, Олег", 
            reply_markup=back_kb
        )
    await call.answer()

# МОДЕРАЦИЯ
@dp.message(Command("mute"))
async def mute_h(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    args = command.args.split(maxsplit=1) if command.args else []
    t = args[0] if len(args)>0 else "1h"
    until = datetime.now() + parse_time(t, 30)
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer(f"🤐 Мут на {t}")
    except Exception as e:
        logging.error(f"Error in mute: {e}")

@dp.message(Command("ban"))
async def ban_h(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    args = command.args.split(maxsplit=1) if command.args else []
    t = args[0] if len(args)>0 else "0"
    try:
        until = datetime.now() + parse_time(t, 1) if t != "0" else None
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id, until_date=until)
        await message.answer(f"💀 Бан {'навсегда' if t=='0' else t}")
    except Exception as e:
        logging.error(f"Error in ban: {e}")

@dp.message(Command("army"))
async def army_h(message: Message):
    if is_admin(message.from_user.id) and message.chat.id in chat_members:
        mentions = [f"[🎖](tg://user?id={u})" for u in list(chat_members[message.chat.id])[:50]]
        await message.answer(f"🚨 **СБОР!**\n\n{' '.join(mentions)}", parse_mode="Markdown")

@dp.message(F.chat.type.in_({"group", "supergroup"}), ~F.text.startswith('/'))
async def collect(message: Message):
    if message.chat.id not in chat_members: chat_members[message.chat.id] = set()
    chat_members[message.chat.id].add(message.from_user.id)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
