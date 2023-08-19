from create_bot import bot, dp, scheduler
from data import Photos, PASSWORD
from keyboards import main_kb, adminMasters_kb, del_sign_kb, back_kb, confirm_kb, show_services, show_calendar, show_time, del_sign_ikb
from DataBase import masters_list, get_photo, get_caption, create_order, del_sign_db
from functions import check_phone, admin_service_notify
from FSM import UserStates, SingStates, DelSignStates
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from datetime import datetime, timedelta


#*** Хендлеры начального состояния пользователя ***#
async def start_command(message: types.Message) -> None:
    await bot.send_message(text='Welocme to {company"s name} bot',
                           reply_markup=await main_kb(),
                           chat_id=message.from_user.id)
    await UserStates.DefaultStatement.set()


async def about_us(message: types.Message) -> None:
    await bot.send_photo(chat_id=message.from_user.id,
                         parse_mode='HTML',
                         photo=Photos[message.text][0],
                         caption=Photos[message.text][1])


async def contacts(message: types.Message) -> None:
    await bot.send_photo(chat_id=message.from_user.id,
                         parse_mode='HTML',
                         photo=Photos[message.text][0],
                         caption=Photos[message.text][1])


#*** Хендлеры записи на прием ***#
async def sing(message: types.Message) -> None:
    await SingStates.Masters.set()
    await message.answer(text='Please, select your master',
                         parse_mode='HTML',
                         reply_markup=await adminMasters_kb())
    

async def get_master(message: types.Message, state: FSMContext) -> None:
    if not message.text == 'Back⬅️' and message.text in [master[0] for master in await masters_list()]:
        try:
            async with state.proxy() as order:
                order['master'] = message.text
                order['count'] = datetime.now().month
                order['year'] = datetime.now().year
                order['ID'] = message.from_user.id
                await bot.send_photo(chat_id=order['ID'],
                                    photo=[photo[0] for photo in await get_photo(order['master'])][0],
                                    caption=[caption[0] for caption in await get_caption(order['master'])][0],
                                    reply_markup=await show_services(order['master']))
                await SingStates.next()
        except ValueError:
            await message.answer(text='There are no masters',
                                 reply_markup= await main_kb())
            await state.finish()
            await UserStates.DefaultStatement.set()
    elif message.text == 'Back⬅️':
        await message.answer(text='Going to menu',
                                 reply_markup= await main_kb())
        await state.finish()
        await UserStates.DefaultStatement.set()
    else:
        await message.answer(text='Incorrect master name, try again',
                                 reply_markup=await adminMasters_kb())
        await SingStates.Masters.set() 


#Где callnack.data от любого сервиса - "его название" - "цена"
async def get_service(callback: types.CallbackQuery, state: FSMContext) -> None:
    async with state.proxy() as order:
        order['service'] = callback.data.split(' - ')[0]
        order['price'] = callback.data.split(' - ')[1]
        order['duration'] = datetime.strptime(callback.data.split(' - ')[2], '%H:%M:%S').time()
        await callback.message.answer(text=f"Service: {order['service']}", 
                                      reply_markup=await back_kb())
        await callback.message.answer(text='Now, choose available date, please',
                                    reply_markup=await show_calendar(name=order['master'], count=order['count'], year=order['year']))
        await SingStates.next()


async def go_back_service(message: types.Message, state: FSMContext):
    if message.text == 'Back⬅️':
        await message.answer(text='Going to menu',
                                 reply_markup= await main_kb())
        await state.finish()
        await UserStates.DefaultStatement.set()


async def get_date(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as order:
        if callback.data == 'next':
            if order['count'] != 12:
                order['count'] += 1
            else:
                order['count'] = 1
                order['year'] += 1
            await bot.edit_message_reply_markup(chat_id=order['ID'], message_id=callback.message.message_id, reply_markup=await show_calendar(name=order['master'], count=order['count'], year=order['year']))
        elif callback.data == 'prev':
            if order['count'] != 1:
                order['count'] -= 1
            else:
                order['count'] = 12
                order['year'] -= 1
            await bot.edit_message_reply_markup(chat_id=order['ID'], message_id=callback.message.message_id, reply_markup=await show_calendar(name=order['master'], count=order['count'], year=order['year']))
        else:
            order['date'] = callback.data #тут дата хранится в формате строки дд.мм
            await SingStates.next()
            await bot.send_message(chat_id=order['ID'], 
                                   text='Now, select the time, please:',
                                   reply_markup=await show_time(data=order['date'], name=order['master']))
            

async def go_back_date(message: types.Message, state: FSMContext):
    if message.text == 'Back⬅️':
        await state.finish()
        await SingStates.Masters.set()
        await message.answer(text='Please, select master again',
                             reply_markup=await adminMasters_kb())


async def get_time(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as order:
        order['time'] = datetime.strptime(callback.data, '%H:%M').time()
        await bot.send_message(chat_id=order['ID'], 
                               text='Please, enter your name:', 
                               reply_markup=await back_kb())
        await SingStates.next()


async def go_back_time(message: types.Message, state: FSMContext):
    async with state.proxy() as order:
        if message.text == 'Back⬅️':
            await SingStates.previous()
            await message.answer(text='Please, select date again',
                                reply_markup=await show_calendar(name=order['master'], count=order['count'], year=order['year']))
            

async def get_FCs(message: types.Message, state: FSMContext):
    async with state.proxy() as order:
        if not message.text == 'Back⬅️':
            order['FCs'] = message.text
            await message.answer(text='Enter your phone, please\nFormat: +7(___)(___)(__)',
                                 reply_markup=await back_kb())
            await SingStates.next()
        else:
            await SingStates.previous()
            await message.answer(text='Now, select the again time, please:',
                                 reply_markup=await show_time(data=order['date'], name=order['master']))


async def get_phone(message: types.Message, state: FSMContext):
    async with state.proxy() as order:
        if not message.text == 'Back⬅️':
            if await check_phone(message.text):
                order['phone'] = message.text
                await message.answer(text=f'-Confirm your order-\nMaster: {order["master"]}\nService: {order["service"]}\nDate and Time: {order["date"]} {str(order["time"])[0:-3]}\nYour"s data: {order["FCs"]}, {order["phone"]}',
                                     reply_markup=await confirm_kb())
                await SingStates.next()
            else:
                await message.answer(text='Try again, incorrect format',
                                     reply_markup=await back_kb())
                await SingStates.Phone.set()
        else:
            await message.answer(text='Enter your name again',
                                 reply_markup=await back_kb())
            await SingStates.previous()


async def get_confirm(message: types.Message, state: FSMContext):
    async with state.proxy() as order:
        if not message.text == 'Назад':
            await message.answer(text='Going back to main menu',
                                 reply_markup=await main_kb())
            await create_order(bot=bot, order=order, scheduler=scheduler)
            scheduler.add_job(admin_service_notify, trigger='date', run_date=(datetime.strptime(f"{order['year']}-{order['date'].split('.')[1]}-{order['date'].split('.')[0]} {str(order['time'])}", '%Y-%m-%d %H:%M:%S')) - timedelta(minutes=30), coalesce=False, kwargs={'bot': bot, 'name':order['FCs'], 'phone':order['phone'], 'serv_name':order['service'], 'serv_price': order['price']})
            await state.finish()
            await UserStates.DefaultStatement.set()
        else:
            await message.answer(text='Type your number again',
                                 reply_markup=await back_kb())
            await SingStates.previous()


#*** Хендлеры удаления записи на прием ***#
async def del_sign(message: types.Message) -> None:
    await message.answer(text='Choose the sign:',
                         reply_markup=await del_sign_ikb(message.from_user.id))
    await DelSignStates.ChooseSign.set()


async def cancel_deleting_sign(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.data == 'Cancel':
        await callback.message.answer(text='Action canceled', reply_markup=await main_kb())
        await state.finish()
        await UserStates.DefaultStatement.set()
    else:
        async with state.proxy() as del_data:
            del_data['service'] = callback.data.split(' - ')[0]
            del_data['date'] = callback.data.split(' - ')[1]
            del_data['order_id'] = int(callback.data.split(' - ')[2])
            del_data['ID'] = int(callback.data.split(' - ')[3])
            await callback.message.answer(text=f'Please, confirm the action\nService: {del_data["service"]}\nDate: {del_data["date"]}', reply_markup=await del_sign_kb())
        await DelSignStates.next()


async def confirm_del_sign(message: types.Message, state: FSMContext):
    if message.text == 'Yes':
        async with state.proxy() as del_data:
            await state.finish()
            await del_sign_db(order_id=del_data['order_id'], user_id=del_data['ID'], bot=bot, scheduler=scheduler)
            await message.answer(text='Sign has deleted successfully!', reply_markup=await main_kb())
            await UserStates.DefaultStatement.set()

    elif message.text == 'No':
        await DelSignStates.previous()
        await message.answer(text='Going back', reply_markup=await del_sign_ikb(message.from_user.id))


def register_handlers_user(dp: Dispatcher):


    #*** Хендлеры начального состояния пользователя ***#
    dp.register_message_handler(start_command, commands=['start'], state=None)
    dp.register_message_handler(about_us, Text('About us🌿') ,state=UserStates.DefaultStatement)
    dp.register_message_handler(contacts, Text('Contacts📞'), state=UserStates.DefaultStatement)


    #*** Хендлеры записи на прием ***#
    dp.register_message_handler(sing, Text('To sign📆'), state=UserStates.DefaultStatement)
    dp.register_message_handler(get_master, content_types=['text'], state=SingStates.Masters)
    dp.register_callback_query_handler(get_service, state=SingStates.Services)
    dp.register_message_handler(go_back_service, state=SingStates.Services)
    dp.register_callback_query_handler(get_date, state=SingStates.Date)
    dp.register_message_handler(go_back_date, state=SingStates.Date)
    dp.register_callback_query_handler(get_time, state=SingStates.Time)
    dp.register_message_handler(go_back_time, state=SingStates.Time)
    dp.register_message_handler(get_FCs, state=SingStates.FCs)
    dp.register_message_handler(get_phone, state=SingStates.Phone)
    dp.register_message_handler(get_confirm, state=SingStates.Confirm)


    #*** Хендлеры удаления записи на прием ***#
    dp.register_message_handler(del_sign, Text('Delete sign❌'), state=UserStates.DefaultStatement)
    dp.register_callback_query_handler(cancel_deleting_sign, state=DelSignStates.ChooseSign)
    dp.register_message_handler(confirm_del_sign, state=DelSignStates.DeleteSign)


    

