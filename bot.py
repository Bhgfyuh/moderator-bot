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

def parse_time(time_str: str):
    try:
        unit = time_str[-1].lower()
        val = int(time_str[:-1])
        if unit == 's': res = timedelta(seconds=val)
        elif unit == 'm': res = timedelta(minutes=val)
        elif unit == 'h': res = timedelta(hours=val)
        elif unit == 'd': res = timedelta(days=val)
        else: res = timedelta(hours=1)
        return max(timedelta(seconds=30), min(res, timedelta(days=365)))
    except: return timedelta(hours=1)

# КНОПКИ
def get_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛡 Модерация", callback_query_data="h_mod")],
        [InlineKeyboardButton(text="🪖 Состав", callback_query_data="h_team")]
    ])

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer("⚔️ **ШТАБ IRON EMPIRE**", reply_markup=get_kb(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("h_"))
async def help_cb(call: CallbackQuery):
    s = call.data.split("_")[1]
    back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_query_data="h_main")]])
    if s == "main": await call.message.edit_text("⚔️ **ШТАБ IRON EMPIRE**", reply_markup=get_kb())
    elif s == "mod": await call.message.edit_text("🛡 **МОД:**\n/mute [время]\n/unmute\n/warn\n/unwarn\n/ban [время]\n/unban [ID]\n/army", reply_markup=back)
    elif s == "team": await call.message.edit_text("🪖 **СОСТАВ:**\nНикита, Арлан, Ярик, Олег", reply_markup=back)
    await call.answer()

# МОДЕРАЦИЯ
@dp.message(Command("mute"))
async def mute_cmd(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    args = command.args.split(maxsplit=1) if command.args else ["1h", ""]
    until = datetime.now() + parse_time(args[0])
    await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False), until_date=until)
    await message.answer(f"🤐 Мут {message.reply_to_message.from_user.first_name}")

@dp.message(Command("ban"))
async def ban_cmd(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    args = command.args.split(maxsplit=1) if command.args else ["0", ""]
    until = (datetime.now() + parse_time(args[0])) if args[0] != "0" else None
    await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id, until_date=until)
    await message.answer(f"💀 Бан {message.reply_to_message.from_user.first_name}")

@dp.message(Command("unmute"))
async def unmute_cmd(message: Message):
    if is_admin(message.from_user.id) and message.reply_to_message:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
        await message.answer("🔊 Размучен.")

@dp.message(Command("unban"))
async def unban_cmd(message: Message, command: CommandObject):
    if is_admin(message.from_user.id) and command.args and command.args.isdigit():
        try:
            await bot.unban_chat_member(message.chat.id, int(command.args), only_if_banned=True)
            await message.answer(f"✅ ID {command.args} разбанен.")
        except Exception as e: await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("warn"))
async def warn_cmd(message: Message):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    warns[uid] = warns.get(uid, 0) + 1
    if warns[uid] >= 3:
        await bot.ban_chat_member(message.chat.id, uid)
        await message.answer(f"🔴 Бан (3/3): {message.reply_to_message.from_user.first_name}")
        warns[uid] = 0
    else: await message.answer(f"⚠️ Варн {message.reply_to_message.from_user.first_name} ({warns[uid]}/3)")

@dp.message(Command("army"))
async def army_cmd(message: Message):
    if is_admin(message.from_user.id) and message.chat.id in chat_members:
        mentions = [f"[🎖](tg://user?id={u})" for u in list(chat_members[message.chat.id])[:50]]
        await message.answer(f"🚨 **СБОР!**\n{' '.join(mentions)}", parse_mode="Markdown")

@dp.message(F.chat.type.in_({"group", "supergroup"}), ~F.text.startswith('/'))
async def collect(message: Message):
    if message.chat.id not in chat_members: chat_members[message.chat.id] = set()
    chat_members[message.chat.id].add(message.from_user.id)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
