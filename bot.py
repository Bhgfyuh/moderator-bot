import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

# Логи в консоль — если упадет, в логах Render будет написано почему
logging.basicConfig(level=logging.INFO)

TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Настройки состава
OWNER_ID = 5349346619
ADMIN_IDS = [5349346619, 5919988510, 5569374433]
demoted_admins = set()
warns = {}
help_cooldown = {}
chat_members = {}

def parse_time(time_str: str):
    if not time_str: return timedelta(hours=1)
    unit = time_str[-1].lower()
    try:
        value = int(time_str[:-1])
        if unit == 's': return timedelta(seconds=value)
        if unit == 'm': return timedelta(minutes=value)
        if unit == 'h': return timedelta(hours=value)
        if unit == 'd': return timedelta(days=value)
    except: return None
    return None

def is_admin(user_id):
    return user_id in ADMIN_IDS and user_id not in demoted_admins

# Сборщик ID (чтобы /army работала)
@dp.message(F.chat.type.in_({"group", "supergroup"}), ~F.text.startswith('/'))
async def collect_members(message: Message):
    cid = message.chat.id
    if cid not in chat_members: chat_members[cid] = set()
    chat_members[cid].add(message.from_user.id)

@dp.message(Command("help"))
async def help_handler(message: Message):
    uid = message.from_user.id
    if not is_admin(uid):
        now = datetime.now()
        last = help_cooldown.get(uid)
        if last and (now - last).total_seconds() < 300:
            try:
                await bot.restrict_chat_member(message.chat.id, uid, ChatPermissions(can_send_messages=False), until_date=now + timedelta(minutes=20))
                return await message.answer("🤫 За спам /help мут 20 мин.")
            except: return
        help_cooldown[uid] = now

    text = (
        "📜 **КОМАНДЫ:**\n"
        "🔹 `/mute [время] [причина]`\n"
        "🔹 `/unmute` / `/warn` / `/unwarn` / `/ban`\n"
        "🔹 `/army [текст]` — Тег всех\n\n"
        "🛡 **СТАРШИЙ СОСТАВ:**\n"
        "👑 Лидер: **Никита**\n"
        "💻 Тех. Админ: **Олег**\n"
        "🎖 Гл. Зам: **Арлан**\n"
        "🥈 Зам: **Ярик**"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("army"))
async def army_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id): return
    cid = message.chat.id
    if cid not in chat_members or not chat_members[cid]:
        return await message.answer("📝 База пуста. Напишите что-нибудь!")
    
    reason = command.args if command.args else "Срочный сбор!"
    emojis = ["🎖","🪖","🔫","🛡"]
    mentions = [f"[{emojis[i % 4]}](tg://user?id={uid})" for i, uid in enumerate(list(chat_members[cid])[:50])]
    
    try:
        msg = await message.answer(f"🚨 **СБОР!**\nПриказ: {reason}\n\n{' '.join(mentions)}", parse_mode="Markdown")
        await bot.pin_chat_message(cid, msg.message_id)
    except: pass

@dp.message(Command("mute"))
async def mute_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    args = command.args.split(maxsplit=1) if command.args else []
    dur = parse_time(args[0] if args else "1h")
    reason = args[1] if len(args) > 1 else "Не указана"
    until = datetime.now() + (dur if dur else timedelta(hours=1))
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer(f"🤐 Мут до {until.strftime('%H:%M')}. Причина: {reason}")
    except Exception as e: await message.answer(f"❌ Ошибка прав: {e}")

@dp.message(Command("warn"))
async def warn_handler(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    warns[uid] = warns.get(uid, 0) + 1
    if warns[uid] >= 3:
        try:
            await bot.ban_chat_member(message.chat.id, uid)
            await message.answer("🔴 Бан за 3/3 варна.")
            warns[uid] = 0
        except: pass
    else:
        await message.answer(f"⚠️ Варн ({warns[uid]}/3). Причина: {command.args or 'Нет'}")

@dp.message(Command("unwarn"))
async def unwarn_handler(message: Message):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    warns[uid] = max(0, warns.get(uid, 0) - 1)
    await message.answer(f"✅ Снят варн. Всего: ({warns[uid]}/3)")

@dp.message(Command("ban"))
async def ban_handler(message: Message):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer("🔴 Забанен.")
    except: pass

@dp.message(Command("unmute"))
async def unmute_handler(message: Message):
    if not is_admin(message.from_user.id) or not message.reply_to_message: return
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
        await message.answer("🔊 Размучен.")
    except: pass

@dp.message(Command("demote"))
async def demote_handler(message: Message):
    if message.from_user.id == OWNER_ID and message.reply_to_message:
        demoted_admins.add(message.reply_to_message.from_user.id)
        await message.answer("🚫 Админ снят.")

@dp.message(Command("promote"))
async def promote_handler(message: Message):
    if message.from_user.id == OWNER_ID and message.reply_to_message:
        target = message.reply_to_message.from_user.id
        if target in demoted_admins: demoted_admins.remove(target)
        await message.answer("✅ Админ восстановлен.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
