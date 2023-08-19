import asyncio
from DataBase import start_DB, admins
from keyboards import order_ikb
from FSM import *
from keyboards import *
from datetime import datetime, date, time
from aiogram import Bot

async def on_startup(_):
    await start_DB()

async def goto_menu(message: types.Message):
    await message.answer(text='Going to main menu!',
                         parse_mode='HTML',
                         reply_markup=main_kb())
    await UserStates.DefaultStatement.set()


async def ask_name(message: types.Message):
    if message.text in [i[0] for i in await masters_list()]:
        await message.answer(text=f'Now select the option for {message.text}:',
                             reply_markup=await admin_kb())
        return message.text
    else:
        return False
    
async def date_check(message: types.Message):
    try:
        return datetime.strptime(message.text, '%d-%m-%Y')
    except ValueError:
        return False
    
async def confirmation(schedule, bot: Bot):
    if len(schedule['date']) > 1 and len(schedule['time']) > 1:
        await bot.send_message(chat_id=schedule['ID'],
                            text=f'Please, confirm the schedule:\nMaster: {schedule["name"]}\nDate: {schedule["date"][0]} - {schedule["date"][-1]}\nTime: {schedule["time"][0]} - {schedule["time"][-2]}',
                            reply_markup=await confirm_kb())
    elif len(schedule['date']) > 1 and len(schedule['time']) == 2:
        await bot.send_message(chat_id=schedule['ID'],
                            text=f'Please, confirm the schedule:\nMaster: {schedule["name"]}\nDate: {schedule["date"][0]} - {schedule["date"][-1]}\nTime: {schedule["time"][0]}',
                            reply_markup=await confirm_kb())
    elif len(schedule['date']) == 1 and len(schedule['time']) == 1:
        await bot.send_message(chat_id=schedule['ID'],
                            text=f'Please, confirm the schedule:\nMaster: {schedule["name"]}\nDate: {datetime.strftime(schedule["date"][0], "%Y-%m-%d")}\nTime: {schedule["time"][0]}',
                            reply_markup=await confirm_kb())
    elif len(schedule['date']) == 1 and len(schedule['time']) > 3:
        await bot.send_message(chat_id=schedule['ID'],
                            text=f'Please, confirm the schedule:\nMaster: {schedule["name"]}\nDate: {schedule["date"][0]}\nTime: {schedule["time"][0]} - {schedule["time"][-2]}',
                            reply_markup=await confirm_kb())
    else:
        print(len(schedule['date']), len(schedule['time']))

async def check_phone(message: str):
    return True if (len(message) >= 12 or len(message) >= 13) and message[0] == '+' else False


async def admin_service_notify(bot: Bot, name, phone, serv_name, serv_price):
    for id in admins:
        await bot.send_message(chat_id=id, text=f'Client: {name}\nPhone number: {phone}\nService"ll be in 30 minutes\n{serv_name} {serv_price}', reply_markup=order_ikb())





