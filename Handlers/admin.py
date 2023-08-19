from create_bot import dp, bot
from data import PASSWORD
from keyboards import preadmin_kb, cancel_kb, adminMasters_kb, DeleteMasters_kb, back_kb, confirm_kb, weekends_kb, service_kb, admin_kb
from DataBase import new_admin, add_master, resign_master, add_schedule, insert_service, delete_service, delete_date, delete_time, get_note, insert_note, format_check ,admins
from functions import ask_name, confirmation
from FSM import AdminStates, UserStates, AddMaster
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import WrongFileIdentifier
import sqlite3 as sq
from datetime import datetime, time


async def check_pass(message: types.Message): #/admin
    await AdminStates.PreAdminState.set()


async def get_admin(message: types.Message): #password check
    if message.text == PASSWORD:
        await message.answer(text='Welcome to admin"s profile',
                             parse_mode='HTML',
                             reply_markup=await preadmin_kb())
        await new_admin(message.from_user.id)
        await AdminStates.next() #AdminActionSelect
    else:
        await message.answer(text='Wrong password')


async def do_action(message: types.Message):
    if message.text == 'Add master':
        await message.answer(text='Please, type master"s name',
                             reply_markup=await cancel_kb())
        await AddMaster.AddName.set()
    elif message.text == 'Select master':
        await message.answer(text='Select the master',
                             reply_markup=await adminMasters_kb())
        await AdminStates.next()
    elif message.text == 'Delete master':
        await message.answer(text='Please, select the master',
                             reply_markup=await DeleteMasters_kb())
        await AdminStates.DeleteMaster.set()


async def order_notify(callback: types.CallbackQuery, state: FSMContext):
    if callback.data.split()[0] == 'confirmed':
        #Возможно удалить эту запись из БД, но в целом хз зачем это делать - Возможно отправить увед клиенту: "не хочет ли он записаться еще? / оцените работу" 
        pass
    elif callback.data.split()[0] == 'add':
        async with state.proxy() as note:
            note['user_id'] = int(callback.data.split()[2])
            for id in admins:
                await bot.send_message(chat_id=id, text='Send new note:', reply_markup=cancel_kb())
            await AdminStates.NoteCreate.set()
    elif callback.data.split()[0] == 'view':
        for id in admins:
            await bot.send_message(chat_id=id, text=get_note())


async def create_note(message: types.Message, state: FSMContext):
    if not message.text == 'Cancel':
        async with state.proxy() as note:
            await insert_note(message.text, note['user_id'])
            await message.answer(text='All are done!', reply_markup=preadmin_kb())
            await state.finish()
            await AdminStates.AdminActionSelect.set()
    else:
        await AdminStates.AdminActionSelect.set()
        await message.answer(text='Action canceled', reply_markup=preadmin_kb())


    #callback_data=f'confirmed {order_id}' / callback_data=f'add comment {user_id}' / callback_data=f'view comment {user_id}'



#Добавляем мастера
async def add_name(message: types.Message, state: FSMContext):
    if not message.text == 'Cancel':
        async with state.proxy() as master_data:
            master_data['name'] = message.text
            await message.answer(text='Please, type master"s phone number\nFormat: +7(...)(...)(..)(..)',
                                 reply_markup=await back_kb())
            await AddMaster.next()
    else:
        await message.answer(text='Action has canceled',
                             reply_markup=await preadmin_kb())
        await AdminStates.AdminActionSelect.set()


async def add_phone(message: types.Message, state: FSMContext):
    async with state.proxy() as master_data:
        if message.text == 'Back⬅️':
            await message.answer(text='Введите имя мастера еще раз',
                            reply_markup=await cancel_kb())
            await AddMaster.previous()
        elif (len(message.text) == 12 or len(message.text == 13)) and message.text[0] == '+':
            master_data['phone'] = message.text
            await message.answer(text='Now, enter URL to add photo',
                                    reply_markup=await back_kb())
            await AddMaster.next()
        else:
            await message.answer(text='Try again, wrong format\nCorrect format: +7(...)(...)(..)(..)',
                        reply_markup=await back_kb())

            

async def add_photo(message: types.Message, state: FSMContext):
    if not message.text == 'Back⬅️':
        async with state.proxy() as master_data:
            master_data['photo'] = message.text
            await message.answer(text='Now, type description for master',
                                 reply_markup=await back_kb())
            await AddMaster.next()
    else:
        await message.answer(text='Now, enter URL to add photo',
                                reply_markup=await back_kb())
        await AddMaster.previous()


async def add_description(message: types.Message, state: FSMContext):
    if not message.text == 'Back⬅️':
        async with state.proxy() as master_data:
            master_data['description'] = message.text
            if await add_master(message=message, master_data=master_data, kb=await preadmin_kb()):
                await message.answer(text='Master has added!',
                                     reply_markup=await preadmin_kb())
                await state.finish()
                await AdminStates.AdminActionSelect.set()
            else:
                await message.answer(text='Something gone wrong, try again', reply_markup=await admin_kb())
                await state.finish()
                await AdminStates.AdminActionSelect.set()
            try:
                await bot.send_photo(chat_id=message.from_user.id, photo=master_data['photo'], caption=master_data['description'])
            except WrongFileIdentifier:
                await AddMaster.previous()
                await message.answer(text='Прешлите ссылку на фото еще раз!', reply_markup=await back_kb())
    else:
        await message.answer(text='Now, type description for master',
                                reply_markup=await back_kb())
        await AddMaster.previous()


#Увольняем мастера
async def get_name(message: types.Message, state: FSMContext):
    if not message.text == 'Cancel':
        async with state.proxy() as delete_master:
            delete_master['name'] = message.text
            await message.answer(text=f'Are you shure?\nYou want to resign: {delete_master["name"]}',
                                 reply_markup=await confirm_kb())
            await AdminStates.DeleteMaster_confirm.set()
    else:
        await message.answer(text='Action has canceled',
                             reply_markup=await preadmin_kb())
        await AdminStates.AdminActionSelect.set()


async def get_confirm(message: types.Message, state: FSMContext):
    if not message.text == 'Назад':
        try:
            async with state.proxy() as delete_master:
                await resign_master(delete_master["name"])
                await message.answer(text=f'{delete_master["name"]} - был уволен',
                                    reply_markup=await preadmin_kb())
                await state.finish()
                await AdminStates.AdminActionSelect.set()
        except sq.OperationalError:
            await message.answer(text='Master does not exist',
                                 reply_markup=await DeleteMasters_kb())
            await AdminStates.DeleteMaster.set()
    else:
        await message.answer(text='Going back',
                             reply_markup=await DeleteMasters_kb())
        await AdminStates.DeleteMaster.set()
 

#Выбираем мастера после кнопки Master select
async def check_name(message: types.Message, state: FSMContext):
    if not message.text == 'Back⬅️':
        async with state.proxy() as schedule:
            schedule['name'] = await ask_name(message)
            schedule['ID'] = message.from_user.id
            schedule['weekends'] = list()
            if schedule['name']:
                await AdminStates.next()
            else:
                await message.answer(text='Name is incorrect, try again!', 
                                     reply_markup=await adminMasters_kb())
    else:
        await message.answer(text='Going back',
                             reply_markup=await preadmin_kb())
        await AdminStates.previous()


#Запрашиваем действие для выбранного мастера
async def req_action(message: types.Message, state: FSMContext):
    if message.text == 'Add schedule':
        await message.answer(text='Now, choose weekends',
                             reply_markup=await weekends_kb())
        await AdminStates.WeekendsReq.set() #Переход в WeekendsReq
    elif message.text == 'delete date from schedule':
        await message.answer(text='Type the date or range of dates, please',
                             reply_markup=await cancel_kb())
        await AdminStates.DateDelete.set()
    elif message.text == 'delete time from date':
        await message.answer(text='Now, type the date please',
                             reply_markup=await cancel_kb())
        await AdminStates.TimeDelete_DateReq.set()
    elif message.text == 'Add service':
        await message.answer(text='Type the service',
                             reply_markup=await cancel_kb())
        await AdminStates.AddService.set()
    elif message.text == 'Delete Service':
        async with state.proxy() as schedule:
            await message.answer(text='Select the service',
                                reply_markup=await service_kb(schedule['name']))
            await AdminStates.ServiceDelete.set()
    elif message.text == 'Back⬅️':
        await message.answer(text='Going back',
                             reply_markup=await adminMasters_kb())
        await AdminStates.AdminStatement.set()


#Кнопка Add schedule
async def req_weekends(message: types.Message, state: FSMContext):
    async with state.proxy() as schedule:
        Day_to_num = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
        
        if not message.text == 'Cancel' and message.text in Day_to_num.keys() and Day_to_num[message.text] in schedule['weekends']:
            schedule['weekends'].remove(Day_to_num[message.text])
            await bot.send_message(chat_id=schedule['ID'],
                                    text=f'{message.text} has deleted from list',
                                    reply_markup=await weekends_kb())
            
        elif not message.text == 'Cancel' and message.text in Day_to_num.keys():
            schedule['weekends'].append(Day_to_num[message.text])
            await bot.send_message(chat_id=schedule['ID'],
                                    text=f'{message.text} has added to list',
                                    reply_markup=await weekends_kb())
            
        elif message.text == 'Next step':
            await message.answer(text='Now, type the date please\nIn format: YYYY-MM-DD\nOr range of dates\nIn format: YYYY-MM-DD - YYYY-MM-DD',
                                 reply_markup=await back_kb())
            await AdminStates.next()

        else:
            await message.answer(text='Action has canceled',
                                 reply_markup=await admin_kb())
            await AdminStates.ActionReq.set()


async def req_date(message: types.Message, state: FSMContext):
            if not message.text == 'Back⬅️':
                async with state.proxy() as schedule:
                    try:
                        if len(message.text) < 11:
                            schedule['date'] = [datetime.strptime(message.text, "%Y-%m-%d")]
                            await message.answer(text='Now, type the time please in format: "HH:MM"\nOr in format: "HH:MM" - "HH:MM"',
                                                reply_markup=await back_kb())
                            await AdminStates.next() #Переход в TimeReq
                        elif len(message.text) > 11:
                            dates = list(map(lambda x: datetime.timestamp(datetime.strptime(x, "%Y-%m-%d")), message.text.split(' - ')))
                            schedule['date'] = list(datetime.strftime(datetime.fromtimestamp(date), "%Y-%m-%d") for date in range(int(dates[0]), int(dates[1])+1, 3600*24))
                            await AdminStates.next() #Переход в TimeReq
                            await message.answer(text='Now, type the time please in format: "HH:MM"\nOr in format: "HH:MM" - "HH:MM"',
                                                reply_markup=await back_kb())
                        else:
                            await message.answer(text='Incorrect date format, please, try again',
                                                reply_markup=await back_kb())
                    except ValueError:
                        await message.answer(text='Incorrect date format, please, try again\nDate format must be: YYYY-MM-DD or YYYY-MM-DD - YYYY-MM-DD',
                                                reply_markup=await back_kb())
            else:
                await AdminStates.previous()
                await message.answer(text='Going back',
                                    reply_markup=await weekends_kb())


async def req_time(message: types.Message, state: FSMContext):
        if not message.text == 'Back⬅️':
            async with state.proxy() as schedule:
                try:
                    if len(message.text) == 4 or len(message.text) == 5:
                        schedule['time'] = [time(hour=int(message.text.split(':')[0]), minute=int(message.text.split(':')[1]))]
                    elif len(message.text) in (11, 12, 13):
                        times = message.text.split(' - ')
                        timer = list()
                        for hour in range(int(times[0].split(':')[0]), int(times[1].split(':')[0])+1):
                            for minute in range(0, 31, 30):
                                timer.append(time(hour=hour, minute=minute))
                        schedule['time'] = timer
                    else:
                        raise ValueError
                    await AdminStates.next()
                    await confirmation(schedule=schedule, bot=bot)
                except ValueError:
                    await message.answer(text=f'Wrong time format, try again!',
                                                 reply_markup=await back_kb())
                    await AdminStates.TimeReq.set()
        else:
            await AdminStates.previous()
            await message.answer(text='Now, type the date please\nIn format: YYYY-MM-DD\nOr range of dates\nIn format: YYYY-MM-DD - YYYY-MM-DD',
                             reply_markup=await back_kb())


async def check_action(message: types.Message, state: FSMContext):
    async with state.proxy() as schedule:
        if message.text == 'Продолжить':
            await add_schedule(schedule)
            await message.answer('Schedule successfuly updated!',
                                 reply_markup=await preadmin_kb())
            await state.finish()
            await AdminStates.AdminActionSelect.set()
        elif message.text == 'Назад':
            await AdminStates.previous()
            await message.answer(text='Now, type the time please in format: "HH:MM"\nOr in format: "HH:MM" - "HH:MM"',
                                 reply_markup=await back_kb())


#Кнопка Add Service
async def add_service(message: types.Message, state: FSMContext):
    if not message.text == 'Cancel':
        async with state.proxy() as schedule:
            schedule['service'] = message.text
            await message.answer(text='Enter the price',
                                reply_markup=await back_kb())
            await AdminStates.AddPrice.set()
    else:
        await message.answer(text='Action has canceled',
                             reply_markup=await admin_kb())
        await AdminStates.ActionReq.set()


async def add_price(message: types.Message, state: FSMContext):
        async with state.proxy() as schedule:
            if not message.text == 'Back⬅️':
                schedule['price'] = message.text
                await message.answer(text='Type duration of the service\nFormat: HH:MM',
                                    reply_markup=await back_kb())
                await AdminStates.AddDuration.set()
            else:
                await message.answer(text='Enter the service again',
                                     reply_markup=await cancel_kb())
                await AdminStates.AddService.set()


async def add_duration(message: types.Message, state: FSMContext):
    async with state.proxy() as schedule:
        if not message.text == 'Back⬅️':
            try:
                schedule['duration'] = time(hour=int(message.text.split(':')[0]), minute=int(message.text.split(':')[1]))
                await message.answer(text=f'Master: {schedule["name"]}\nService: {schedule["service"]}\nPrice: {schedule["price"]}\nDuration: {schedule["duration"]}\nHas added!',
                                     reply_markup=await admin_kb())
                await insert_service(service=schedule["service"], price=schedule['price'], duration=str(schedule['duration']), name=schedule['name'])
                await AdminStates.ActionReq.set()
            except ValueError:
                await message.answer(text='Wrong time format, try again\nFormat: HH:MM')
                await AdminStates.AddDuration.set()
        else:
            await message.answer(text='Type price again',
                                 reply_markup=await back_kb())


#Delete service button
async def del_service(message: types.Message, state:FSMContext):
    if not message.text == 'Cancel':
        async with state.proxy() as schedule:
            try:
                await delete_service(service=message.text, name=schedule['name'])
                await message.answer(text=f'Service: {message.text}\nFor master: {schedule["name"]}\nHas deleted!',
                                     reply_markup=await admin_kb())
                await AdminStates.ActionReq.set()
            except sq.IntegrityError:
                await message.answer(text='Service not found', reply_markup=await admin_kb())
                await AdminStates.ActionReq.set()
    else:
        await message.answer(text='Going back',
                             reply_markup=await admin_kb())
        await AdminStates.ActionReq.set()


#Кнопка Delete date from schedule
async def del_date(message: types.Message, state: FSMContext):
    async with state.proxy() as schedule:
        if not message.text == 'Cancel':
            schedule['del_date'] = message.text
            await delete_date(schedule['del_date'], schedule['name'])
            await message.answer(text=f'This date has deleted from schedule: {schedule["del_date"]}',
                                 reply_markup=await admin_kb())
            await AdminStates.ActionReq.set()
        else:
            await message.answer(text='Action canceled',
                                 reply_markup=await admin_kb())
            await AdminStates.ActionReq.set()


#Delete time from date #Cancel переводит в ActionReq и запускает admin_kb
async def get_date(message: types.Message, state: FSMContext):
    if not message.text == 'Cancel':
        async with state.proxy() as schedule:
            try:
                schedule['date_delete'] = message.text
                await message.answer(text='Now, type the time',
                                     reply_markup=await back_kb())
                await AdminStates.next() # To TimeDelete state
            except ValueError:
                await message.answer(text='Wrong date format\nTry again!',
                                     reply_markup=await cancel_kb())
                await AdminStates.TimeDelete_DateReq.set()
    else:
        await message.answer(text='Action has canceled',
                             reply_markup=await admin_kb())
        await AdminStates.ActionReq.set()


async def del_time(message: types.Message, state: FSMContext):
    if not message.text == 'Back⬅️':
        async with state.proxy() as schedule:
            if await format_check(schedule['date_delete'], message.text):
                schedule['time_delete'] = message.text
                await delete_time(date=schedule['date_delete'], time=schedule['time_delete'], name=schedule['name'])
                await message.answer(text=f'Master: {schedule["name"]}\nDate: {schedule["date_delete"]}\nTime: {schedule["time_delete"]}\nHas deleted!',
                                     reply_markup=await preadmin_kb())
                await state.finish()
                await AdminStates.AdminActionSelect.set()
            else:
                await message.answer(text='Wrong time format\nTry again!',
                                     reply_markup=await back_kb())
                await AdminStates.TimeDelete.set()
    else:
        await message.answer(text='Going back',
                             reply_markup=await cancel_kb())
        await AdminStates.TimeDelete_DateReq.set()


def register_handlers_admin(dp: Dispatcher):


    #*** Хендлеры перед выбором действия в админке ***#
    dp.register_message_handler(check_pass, commands=['admin'], state=UserStates.DefaultStatement)
    dp.register_message_handler(get_admin, state=AdminStates.PreAdminState)
    dp.register_message_handler(do_action, state=AdminStates.AdminActionSelect)


    #*** Хендлеры перед выбором действия в админке ***#
    dp.callback_query_handler(order_notify, state=AdminStates.AdminActionSelect)
    dp.register_message_handler(create_note, state=AdminStates.NoteCreate)


    #*** Хендлеры добавления мастера ***#
    dp.register_message_handler(add_name, state=AddMaster.AddName)
    dp.register_message_handler(add_phone, state=AddMaster.AddPhone)
    dp.register_message_handler(add_photo, state=AddMaster.AddPhoto)
    dp.register_message_handler(add_description, state=AddMaster.AddDescription)


    #*** Хендлеры увольнения мастера ***#
    dp.register_message_handler(get_name, state=AdminStates.DeleteMaster)
    dp.register_message_handler(get_confirm, state=AdminStates.DeleteMaster_confirm)


    #*** Хендлеры кнопки select master ***#
    dp.register_message_handler(check_name, state=AdminStates.AdminStatement)
    dp.register_message_handler(req_action, state=AdminStates.ActionReq)


    #*** Хендлеры кнопки select master-add schedule ***#
    dp.register_message_handler(req_weekends, state=AdminStates.WeekendsReq)
    dp.register_message_handler(req_date, state=AdminStates.DateReq)
    dp.register_message_handler(req_time, state=AdminStates.TimeReq)
    dp.register_message_handler(check_action, state=AdminStates.Confirmation)


    #*** Хендлеры кнопки select master-add service ***#
    dp.register_message_handler(add_service, state=AdminStates.AddService)
    dp.register_message_handler(add_price, state=AdminStates.AddPrice)
    dp.register_message_handler(add_duration, state=AdminStates.AddDuration)


    #*** Хендлеры кнопки select master-delete service ***#
    dp.register_message_handler(del_service, state=AdminStates.ServiceDelete)


    #*** Хендлеры кнопки select master-delete date ***#
    dp.register_message_handler(del_date, state=AdminStates.DateDelete)


    #*** Хендлеры кнопки select master-delete time ***#
    dp.register_message_handler(get_date, state=AdminStates.TimeDelete_DateReq)
    dp.register_message_handler(del_time, state=AdminStates.TimeDelete)