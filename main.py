import logging


import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import router, user_data
import utils


from dotenv import load_dotenv
import os

load_dotenv()  

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


async def main():
    logging.basicConfig(level=logging.INFO)


    global user_data
    loaded_data = utils.load_data_from_json()
    if loaded_data:
        user_data.update(loaded_data)
        logging.info("Данные загружены из JSON.")


    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())


    dp.include_router(router)

 
    logging.info("Бот запущен. Нажмите Ctrl+C для остановки.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
