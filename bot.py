import asyncio
import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command

# ВСТАВЬ СВОЙ ТОКЕН СЮДА:
TOKEN = '8714415957'

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def is_admin(message: Message) -> bool:
    member = await message.chat.get_member(message.from_user.id)
    return member.status in ['administrator', 'creator']

@dp.message(Command("ban"), F.reply_to_message)
async def ban_user(message: Message):
    if not await is_admin(message): return
    target = message.reply_to_message
    await bot.ban_chat_member(chat_id=message.chat.id, user_id=target.from_user.id)
    await message.answer(f"🔴 {target.from_user.first_name} отправлен в бан!")

@dp.message(Command("mute"), F.reply_to_message)
async def mute_user(message: Message):
    if not await is_admin(message): return
    target = message.reply_to_message
    args = message.text.split()
    duration = int(args[1]) if len(args) > 1 and args[1].isdigit() else 15
    
    until_date = datetime.datetime.now() + datetime.timedelta(minutes=duration)
    await bot.restrict_chat_member(
        chat_id=message.chat.id, 
        user_id=target.from_user.id, 
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until_date
    )
    await message.answer(f"🤐 {target.from_user.first_name} замучен на {duration} мин.")

@dp.message(Command("unmute"), F.reply_to_message)
async def unmute_user(message: Message):
    if not await is_admin(message): return
    target = message.reply_to_message
    permissions = ChatPermissions(can_send_messages=True, can_send_audios=True, can_send_documents=True, can_send_photos=True, can_send_videos=True, can_send_video_notes=True, can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True)
    await bot.restrict_chat_member(chat_id=message.chat.id, user_id=target.from_user.id, permissions=permissions)
    await message.answer(f"🔊 {target.from_user.first_name} снова может говорить.")

warns_storage = {}

@dp.message(Command("warn"), F.reply_to_message)
async def warn_user(message: Message):
    if not await is_admin(message): return
    target = message.reply_to_message
    key = (message.chat.id, target.from_user.id)
    warns_storage[key] = warns_storage.get(key, 0) + 1
    
    if warns_storage[key] >= 3:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target.from_user.id)
        warns_storage[key] = 0
        await message.answer(f"☠️ {target.from_user.first_name} получил 3/3 варнов и был забанен!")
    else:
        await message.answer(f"⚠️ Предупреждение {target.from_user.first_name} [{warns_storage[key]}/3].")

async def main():
    print("Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())