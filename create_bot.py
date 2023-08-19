from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

storage = MemoryStorage()
bot = Bot(token='6384126673:AAHM0KEuYldcuQUWlw-isqtHwp_KV9xLXxI')
dp = Dispatcher(bot, storage=storage)
scheduler = AsyncIOScheduler()
