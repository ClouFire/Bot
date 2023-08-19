import asyncio
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import types
from DataBase import masters_list, service_list, get_service, avalibale_dates_list, get_time_list, show_signs
from FSM import *
from datetime import datetime, date
import locale

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


async def main_kb() -> ReplyKeyboardMarkup:  # Main keyboard func
    main_kb = ReplyKeyboardMarkup(resize_keyboard=True)

    btn_aboutus = KeyboardButton(text='About us🌿')
    btn_cont = KeyboardButton(text='Contacts📞')
    btn_sign = KeyboardButton(text='To sign📆')
    btn_cancel = KeyboardButton(text='Delete sign❌')

    main_kb.row(btn_aboutus, btn_cont).row(btn_sign, btn_cancel)

    return main_kb


async def del_sign_ikb(id) -> InlineKeyboardMarkup:
    del_sign_kb = InlineKeyboardMarkup()

    SIGNS = await show_signs(id)

    for service, date, order_id in SIGNS:
        del_sign_kb.add(InlineKeyboardButton(text=f'{service} / {date}', callback_data=f'{service} - {date} - {order_id} - {id}'))

    del_sign_kb.add(InlineKeyboardButton(text='❌Cancel❌', callback_data='Cancel'))

    return del_sign_kb


async def del_sign_kb() -> ReplyKeyboardMarkup:
    del_sign_kb = ReplyKeyboardMarkup(resize_keyboard=True)

    del_sign_kb.row(KeyboardButton(text='Yes'), KeyboardButton(text='No'))

    return del_sign_kb


async def sing_masters_kb() -> ReplyKeyboardMarkup:
    sing_masters_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    MASTERS = [master[0] for master in await masters_list()]

    btn_main = KeyboardButton(text='⬅️Main menu⬅️')

    if len(MASTERS) == 1:
        sing_masters_kb.add(MASTERS[0])
        sing_masters_kb.add(btn_main)
    elif len(MASTERS) % 2 == 0:
        for master in range(0, len(MASTERS), 2):
            sing_masters_kb.row(master, master+1)
        sing_masters_kb.add(btn_main)
    elif len(MASTERS) % 2 != 0 and len(MASTERS) > 1:
        for master in range(0, len(MASTERS)-1, 2):
            sing_masters_kb.row(master, master+1)
        sing_masters_kb.row(MASTERS[-1], btn_main)
    else:
        raise ValueError
    
    return sing_masters_kb


async def show_services(name) -> InlineKeyboardMarkup:
    show_services = InlineKeyboardMarkup()

    for service, price, duration in await get_service(name):
        show_services.add(InlineKeyboardButton(text=f'{service} - {price}rub.', callback_data=f'{service} - {price} - {duration}'))
    
    return show_services


async def show_calendar(name, count, year) -> InlineKeyboardMarkup:
    show_calendar = InlineKeyboardMarkup()

    show_calendar.row(InlineKeyboardButton(text='<', callback_data='prev'), InlineKeyboardButton(text=f'{(date(year, count, 1).strftime("%b. %Y"))}.'.capitalize(), callback_data='None'), InlineKeyboardButton(text='>', callback_data='next'))

    days = await avalibale_dates_list(name, count, year)
    calendar = [0]*31

    for day in days:
        calendar[int(day)-1] = day
        

    for i in range(4):
        show_calendar.row(InlineKeyboardButton(text=f'{calendar[0+(i*7)] if calendar[0+(i*7)] else " "}', callback_data=f"{calendar[0+(i*7)]}.{count}"), 
                          InlineKeyboardButton(text=f'{calendar[1+(i*7)] if calendar[1+(i*7)] else " "}', callback_data=f"{calendar[1+(i*7)]}.{count}"), 
                          InlineKeyboardButton(text=f'{calendar[2+(i*7)] if calendar[2+(i*7)] else " "}', callback_data=f"{calendar[2+(i*7)]}.{count}"), 
                          InlineKeyboardButton(text=f'{calendar[3+(i*7)] if calendar[3+(i*7)] else " "}', callback_data=f"{calendar[3+(i*7)]}.{count}"), 
                          InlineKeyboardButton(text=f'{calendar[4+(i*7)] if calendar[4+(i*7)] else " "}', callback_data=f"{calendar[4+(i*7)]}.{count}"), 
                          InlineKeyboardButton(text=f'{calendar[5+(i*7)] if calendar[5+(i*7)] else " "}', callback_data=f"{calendar[5+(i*7)]}.{count}"), 
                          InlineKeyboardButton(text=f'{calendar[6+(i*7)] if calendar[6+(i*7)] else " "}', callback_data=f"{calendar[6+(i*7)]}.{count}"))

    show_calendar.row(InlineKeyboardButton(text=f'{calendar[-3] if calendar[-3] else " "}', callback_data=f"{calendar[-3]}.{count}"), 
                      InlineKeyboardButton(text=f'{calendar[-2] if calendar[-2] else " "}', callback_data=f"{calendar[-2]}.{count}"), 
                      InlineKeyboardButton(text=f'{calendar[-1] if calendar[-1] else " "}', callback_data=f"{calendar[-1]}.{count}"))

    return show_calendar


async def show_time(data, name) -> InlineKeyboardMarkup:
    show_time = InlineKeyboardMarkup()

    TIME = await get_time_list(data=data, name=name)

    for time in range(len(TIME) // 4):
        show_time.row(InlineKeyboardButton(text=f"{TIME[0+(time*4)]}", callback_data=f'{TIME[0+(time*4)]}'), InlineKeyboardButton(text=f"{TIME[1+(time*4)]}", callback_data=f'{TIME[1+(time*4)]}'), InlineKeyboardButton(text=f"{TIME[2+(time*4)]}", callback_data=f'{TIME[2+(time*4)]}'), InlineKeyboardButton(text=f"{TIME[3+(time*4)]}", callback_data=f'{TIME[3+(time*4)]}'))
    if len(TIME) % 4 == 3:
        show_time.row(InlineKeyboardButton(text=f"{TIME[-3]}", callback_data=f'{TIME[-3]}'), InlineKeyboardButton(text=f"{TIME[-2]}", callback_data=f'{TIME[-2]}'), InlineKeyboardButton(text=f"{TIME[-1]}", callback_data=f'{TIME[-1]}'))
    elif len(TIME) % 4 == 2:
        show_time.row(InlineKeyboardButton(text=f"{TIME[-2]}", callback_data=f'{TIME[-2]}'), InlineKeyboardButton(text=f"{TIME[-1]}", callback_data=f'{TIME[-1]}'))
    elif len(TIME) % 4 == 1:
        show_time.row(InlineKeyboardButton(text=f"{TIME[-1]}", callback_data=f'{TIME[-1]}'))

    return show_time


#admins kb
async def masters_kb() -> ReplyKeyboardMarkup:
    m_kb = ReplyKeyboardMarkup(resize_keyboard=True)

    btn_menu = KeyboardButton(text='⬅️Main menu⬅️')

    MASTER = list(i for i in await masters_list())
    if len(MASTER) % 2 == 0:
        for master in range(0, len(MASTER), 2):
            m_kb.row(MASTER[master], MASTER[master+1])
        m_kb.add(btn_menu)
    else:
        for master in range(0, len(MASTER)-1, 2):
            m_kb.row(MASTER[master], MASTER[master+1])
        m_kb.add(MASTER[len(MASTER)-1])
        m_kb.add(btn_menu)

    return m_kb


async def weekends_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True).row(KeyboardButton(text='Monday'),KeyboardButton(text='Tuesday')).row(KeyboardButton(text='Wednesday'),KeyboardButton(text='Thursday')).row(KeyboardButton(text='Friday'),KeyboardButton(text='Saturday')).row(KeyboardButton(text='Sunday'),KeyboardButton(text='Cancel')).add(KeyboardButton(text='Next step'))


async def preadmin_kb() -> ReplyKeyboardMarkup:
    preadmin_kb = ReplyKeyboardMarkup(resize_keyboard=True)

    btn_add = KeyboardButton(text='Add master')
    btn_select = KeyboardButton(text='Select master')
    btn_del = KeyboardButton(text='Delete master')

    preadmin_kb.row(btn_add, btn_del).add(btn_select)
    
    return preadmin_kb


async def admin_kb() -> ReplyKeyboardMarkup:
    admin_kb = ReplyKeyboardMarkup(resize_keyboard=True)

    btn_date_create = KeyboardButton(text='Add schedule')
    btn_delete_dates = KeyboardButton(text='delete date from schedule')
    btn_delete_time = KeyboardButton(text='delete time from date')
    btn_service = KeyboardButton(text='Add service')
    btn_back = KeyboardButton(text='Back⬅️')
    btn_delservice = KeyboardButton(text='Delete Service')

    admin_kb.row(btn_date_create, btn_service).row(btn_delete_dates, btn_delete_time).add(btn_delservice).add(btn_back)

    return admin_kb


async def adminMasters_kb() -> ReplyKeyboardMarkup:
    adminMasters_kb = ReplyKeyboardMarkup(resize_keyboard=True)

    MASTERS = await masters_list()

    for master in MASTERS:
        adminMasters_kb.add(KeyboardButton(text=f'{master[0]}'))
    adminMasters_kb.add(KeyboardButton(text='Back⬅️'))
    return adminMasters_kb


async def DeleteMasters_kb() -> ReplyKeyboardMarkup:
    adminMasters_kb = ReplyKeyboardMarkup(resize_keyboard=True)

    MASTERS = await masters_list()

    for master in MASTERS:
        adminMasters_kb.add(KeyboardButton(text=f'{master[0]}'))
    adminMasters_kb.add(KeyboardButton(text='Cancel'))
    return adminMasters_kb


async def confirm_kb() -> ReplyKeyboardMarkup:
    confirm_kb = ReplyKeyboardMarkup(resize_keyboard=True)

    btn_yes = KeyboardButton(text='Продолжить')
    btn_no = KeyboardButton(text='Назад')


    confirm_kb.row(btn_yes, btn_no)
    return confirm_kb


async def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(text='Cancel'))


async def back_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(text='Back⬅️'))


async def service_kb(name) -> ReplyKeyboardMarkup:
    service_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for service in await service_list(name):
        service_kb.add(KeyboardButton(text=f'{service[0]}'))
    service_kb.add(KeyboardButton(text='Cancel'))
    return service_kb


async def order_ikb(order_id, user_id) -> InlineKeyboardMarkup:
    order_ikb = InlineKeyboardMarkup()

    order_ikb.add(InlineKeyboardButton(text='Визит состоялся', callback_data=f'confirmed {order_id}'), InlineKeyboardButton(text='Добавить комментарий', callback_data=f'add comment {user_id}'), InlineKeyboardButton(text='Просмотреть комментарий', callback_data=f'view comment {user_id}'))

    return order_ikb