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

# СПИСОК АДМИНОВ
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

# КНОПКИ
def get_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛡 Модерация", callback_query_data="h_mod")],
        [InlineKeyboardButton(text="🪖 Старший Состав", callback_query_data="h_team")]
    ])

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer("⚔️ **ШТАБ IRON EMPIRE**\nВыберите раздел:", reply_markup=get_kb(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("h_"))
async def help_cb(call: CallbackQuery):
    s = call.data.split("_")[1]
    back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_query_data="h_main")]])
    if s == "main":
        await call.message.edit_text("⚔️ **ШТАБ IRON EMPIRE**", reply_markup=get_kb())
    elif s == "mod":
        await call.message.edit_text(
            "🛡 **МОДЕРАЦИЯ (ОТВЕТОМ):**\n\n"
            "🚫 `/mute [время] [причина]` (30с-365д)\n"
            "🔊 `/unmute` — снять мут\n"
            "⚠️ `/warn [причина]` — выдать пред\n"
            "✅ `/unwarn` — снять пред\n"
            "💀 `/ban [время] [причина]` (1с-365д)\n"
            "🔓 `/unban [ID]` — разбанить\n"
            "🚩 `/army` — сбор состава", reply_markup=back, parse_mode="Markdown")
    elif s == "team":
        await call.message.edit_text(
            "🪖 **СТАРШИЙ СОСТАВ:**\n\n"
            "👑 **Никита** — Лидер\n"
            "🎖 **Арлан** — Гл. Заместитель\n"
            "🥈 **Ярик** — Заместитель\n"
            "🥈 **Вакансия** — Заместитель\n"
            "🥈 **Вакансия** — Заместитель\n"
            "💻 **Олег** — Тех. Админ", reply_markup=back, parse_mode="Markdown")
    await call.answer()

# МОДЕРАЦИЯ
@dp.message(Command("mute"))
async def mute_h(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    args = command.args.split(maxsplit=1) if command.args else []
    t, r = (args[0] if len(args)>0 else "1h"), (args[1] if len(args)>1 else "Не указана")
    until = datetime.now() + parse_time(t, 30)
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer(f"🤐 **МУТ:** {message.reply_to_message.from_user.first_name}\n⏰ **Срок:** {t}\n📝 **Причина:** {r}")
    except: pass

@dp.message(Command("ban"))
async def ban_h(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    args = command.args.split(maxsplit=1) if command.args else []
    t, r = (args[0] if len(args)>0 else "0"), (args[1] if len(args)>1 else "Не указана")
    try:
        until = datetime.now() + parse_time(t, 1) if t != "0" else None
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id, until_date=until)
        await message.answer(f"💀 **БАН:** {message.reply_to_message.from_user.first_name}\n⏰ **Срок:** {t if t!='0' else 'Навсегда'}\n📝 **Причина:** {r}")
    except: pass

@dp.message(Command("unmute"))
async def unmute_h(message: Message):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
    await message.answer("🔊 Мут снят!")

@dp.message(Command("unban"))
async def unban_h(message: Message, command: CommandObject):
    if is_admin(message.from_user.id) and command.args:
        try:
            await bot.unban_chat_member(message.chat.id, int(command.args), only_if_banned=True)
            await message.answer(f"🔓 ID {command.args} разбанен.")
        except: pass

@dp.message(Command("warn"))
async def warn_h(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    warns[uid] = warns.get(uid, 0) + 1
    if warns[uid] >= 3:
        await bot.ban_chat_member(message.chat.id, uid)
        await message.answer(f"🔴 **БАН (3/3):** {message.reply_to_message.from_user.first_name}")
        warns[uid] = 0
    else:
        await message.answer(f"⚠️ **ВАРН ({warns[uid]}/3):** {message.reply_to_message.from_user.first_name}\n📝 **Причина:** {command.args or 'Не указана'}")

@dp.message(Command("unwarn"))
async def unwarn_h(message: Message):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    warns[uid] = max(0, warns.get(uid, 0) - 1)
    await message.answer(f"✅ Варн снят. Счёт: {warns[uid]}/3")

@dp.message(Command("army"))
async def army_h(message: Message):
    if is_admin(message.from_user.id) and message.chat.id in chat_members:
        mentions = [f"[🎖](tg://user?id={u})" for u in list(chat_members[message.chat.id])[:50]]
        msg = await message.answer(f"🚨 **СБОР!**\n\n{' '.join(mentions)}", parse_mode="Markdown")
        try: await bot.pin_chat_message(message.chat.id, msg.message_id)
        except: pass

@dp.message(F.chat.type.in_({"group", "supergroup"}), ~F.text.startswith('/'))
async def collect(message: Message):
    if message.chat.id not in chat_members: chat_members[message.chat.id] = set()
    chat_members[message.chat.id].add(message.from_user.id)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
