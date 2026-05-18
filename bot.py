import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiohttp import web

# ТОКЕН
TOKEN = '8714415957:AAFEY7J5P-73GwtC9eBTOL9NgCaimwGcGrU'

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Бот запущен и готов к модерации!")

# Хелсчек для Render (чтобы не выдавал ошибку Port Scan)
async def handle(request):
    return web.Response(text="Bot is alive")

async def main():
    # Запуск мини-сервера для Render на порту 10000
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    asyncio.create_task(site.start())
    
    print("Бот погнал!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
