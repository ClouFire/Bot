from create_bot import dp, scheduler, bot
from DataBase import daily_notify, delete_orders, admins
from functions import on_startup
from Handlers import user, admin
from aiogram import executor
import asyncio
import logging


logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)




if __name__ == '__main__':

    user.register_handlers_user(dp)
    admin.register_handlers_admin(dp)

    scheduler.start()
    for id in admins:
        scheduler.add_job(daily_notify, trigger='cron', hour=6, minute=30, kwargs={'bot': bot, 'chat_id': id})
    scheduler.add_job(delete_orders, trigger='cron', month=1)
    asyncio.run(executor.start_polling(dp,
                           skip_updates=True,
                           on_startup=on_startup))

    asyncio.get_event_loop().run_forever()
