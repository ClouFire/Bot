import sqlite3 as sq
from aiogram import types, Bot
from datetime import datetime, timedelta, date, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

admins = [702421502]


async def start_DB():
    global DB, CURSOR

    DB = sq.connect('ProjectDB.sqlite')
    CURSOR = DB.cursor()


    CURSOR.execute("PRAGMA foreign_keys = ON")


    CURSOR.execute(
        '''CREATE TABLE IF NOT EXISTS book(order_id INTEGER PRIMARY KEY,
            name VARCHAR(30),
            phone VARCHAR(13),
            id INT,
            service VARCHAR(30),
            duration VARCHAR(8),
            date DATETIME,
            master VARCHAR(30),
            price INT
            )''')

    CURSOR.execute(
        '''CREATE TABLE IF NOT EXISTS master(
            name VARCHAR(30) PRIMARY KEY,
            phone VARCHAR(13),
            photo TEXT,
            description TEXT
            )''')

    CURSOR.execute(
        '''CREATE TABLE IF NOT EXISTS client(
            user_id INT PRIMARY KEY,
            name VARCHAR(30),
            phone VARCHAR(13),
            note TEXT
            )''')

    CURSOR.execute(
        '''CREATE TABLE IF NOT EXISTS service(
            service VARCHAR(30) PRIMARY KEY,
            price INT,
            duration VARCHAR(8),
            master_name VARCHAR(30),
            FOREIGN KEY (master_name) REFERENCES master(name)
            )''')
    
    CURSOR.execute(
        '''CREATE TABLE IF NOT EXISTS admin(
            admin_id INTEGER PRIMARY KEY
            )''')

    DB.commit()


async def create_order(order, bot: Bot, scheduler: AsyncIOScheduler):
    times_to_del = list()
    try:
        CURSOR.execute("INSERT INTO client(user_id, name, phone, note) VALUES(?, ?, ?, NULL)", [order['ID'], order['FCs'], order['phone']])
        DB.commit()
    except sq.IntegrityError:
        pass
    CURSOR.execute("INSERT INTO book(order_id, name, phone, id, service, duration, date, master, price) VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?)", [order['FCs'], order['phone'], int(order['ID']), order['service'], str(order['duration']), datetime.combine(datetime.strptime(f"{order['year']}-{order['date'].split('.')[1]}-{order['date'].split('.')[0]}", '%Y-%m-%d').date(), order['time']), order['master'], order['price']])
    for hour in range(order['time'].hour, order['time'].hour + order['duration'].hour + 1, 1):
        for minute in range(0, 31, 30):
            times_to_del.append(time(hour=hour, minute=minute))

    if order['time'].minute == 0 and order['duration'].minute == 0:
        times_to_del = times_to_del[0:-1]
    elif order['time'].minute == 30:
        if order['duration'].minute == 0:
            times_to_del = times_to_del[1::]
        elif order['duration'].minute == 30:
            times_to_del = times_to_del[1::]
            times_to_del.append(time(hour=times_to_del[-1].hour+1))
    
    for elem in times_to_del:
        CURSOR.execute(f"DELETE FROM {order['master']}_schedule WHERE strftime('%Y-%m-%d', date)=? AND strftime('%H:%M:%S', date)=?", [datetime.strptime(f"{order['year']}-{order['date'].split('.')[1]}-{order['date'].split('.')[0]}", '%Y-%m-%d').date(), str(elem)])
        DB.commit()

    if not len(list(CURSOR.execute(f"SELECT order_id FROM book WHERE name=? AND phone=?", [order['FCs'], order['phone']]))) or datetime.combine(datetime.strptime(f"{order['year']}-{order['date'].split('.')[1]}-{order['date'].split('.')[0]}", '%Y-%m-%d').date(), order['time']) > datetime.strptime([time[0] for time in CURSOR.execute("SELECT MAX(date) FROM book WHERE name=? AND phone=?", [order['FCs'], order['phone']])][0], '%Y-%m-%d %H:%M:%S'):
        for id in [id[0] for id in CURSOR.execute(f"SELECT admin_id FROM admin")]:
            await bot.send_message(chat_id=id, text=f'New sign!\nMaster: {order["master"]}\nDate and time: {order["date"]} {order["time"]}\nService: {order["service"]}\nName and number: {order["FCs"]} / {order["phone"]}')
        scheduler.add_job(send_notify, trigger='date', kwargs={'bot': bot, 'chat_id': int(order['ID'])}, replace_existing=True, coalesce=True, run_date=(datetime.strptime(f"{order['year']}-{order['date'].split('.')[1]}-{order['date'].split('.')[0]}", '%Y-%m-%d') + timedelta(weeks=3, hours=9)), id=f'{order["ID"]}_first')
        scheduler.add_job(send_notify, trigger='date', kwargs={'bot': bot, 'chat_id': int(order['ID'])}, replace_existing=True, coalesce=True, run_date=(datetime.strptime(f"{order['year']}-{order['date'].split('.')[1]}-{order['date'].split('.')[0]}", '%Y-%m-%d') + timedelta(weeks=5, hours=9)), id=f'{order["ID"]}_second')
    scheduler.add_job(client_service_notify, trigger='date', kwargs={'bot': bot, 'chat_id': int(order['ID']), 'date': order['date'], 'time': order['time']}, run_date=datetime.combine((datetime.strptime(f"{order['year']}-{order['date'].split('.')[1]}-{order['date'].split('.')[0]}", '%Y-%m-%d')).date(), order['time']), id=f"{tuple(CURSOR.execute('SELECT order_id FROM book WHERE date=? AND master=? AND name=?', [datetime.combine(datetime.strptime(str(order['year'])+'-'+str(order['date'].split('.')[1])+'-'+str(order['date'].split('.')[0]), '%Y-%m-%d').date(), order['time']), order['master'], order['FCs']]))[0][0]}_service")

#если что можно будет разделить эту функцию внутри работы на две и отправлять через 3 недели одно сообщение, а через 5 недель - другое
async def send_notify(bot: Bot, chat_id: int):
    await bot.send_message(chat_id=chat_id, text='Some message')


async def client_service_notify(bot: Bot, chat_id: int, date, time):
    await bot.send_message(chat_id=chat_id, text=f'Your date has come!\nI"ve registred to a service at: {date} in: {datetime.strftime(time, "%H:%M")}')
    

async def get_note(user_id):
    return tuple(CURSOR.execute("SELECT note FROM client WHERE user_id=?", [user_id]))[0][0] if len(tuple(CURSOR.execute("SELECT note FROM client WHERE user_id=?", [user_id]))) else 'There is no any note'
    

async def insert_note(text, user_id):
    CURSOR.execute("INSERT INTO client VALUES(NULL, NULL, NULL, ?) WHERE user_id=?", [text, user_id])



async def new_admin(id):
    try:
        CURSOR.execute(f"INSERT INTO admin VALUES(?)", [id])
    except sq.IntegrityError:
        pass
    DB.commit()


async def add_schedule(schedule):
    if len(schedule['date']) == 1 and len(schedule['time']) == 1:
        try:
            CURSOR.execute(f"INSERT INTO {schedule['name']}_schedule(date, master) VALUES(?, ?)",[datetime.combine(schedule['date'][0], schedule['time'][0]), schedule['name']])
        except sq.IntegrityError:
            pass
    elif len(schedule['date']) == 1 and len(schedule['time']) > 1:
        for time in schedule['time'][0:-1]:
            if schedule['date'][0].weekday() not in schedule['weekends']:
                try:
                    CURSOR.execute(f"INSERT INTO {schedule['name']}_schedule(date, master) VALUES(?, ?)",[datetime.combine(schedule['date'][0], time), schedule['name']])
                except sq.IntegrityError:
                    pass
    elif len(schedule['date']) > 1 and len(schedule['time']) == 1:
        for date in schedule['date']:
            if date.weekday() not in schedule['weekends']:
                CURSOR.execute(f"INSERT INTO {schedule['name']}_schedule(date, master) VALUES(?, ?)",[datetime.combine(date, schedule["time"][0]), schedule['name']])
    else:
        for date in schedule['date']:
            for time in schedule['time'][0:-1]:
                if datetime.strptime(date, '%Y-%m-%d').weekday() not in schedule['weekends']:
                    try:
                        CURSOR.execute(f"INSERT INTO {schedule['name']}_schedule(date, master) VALUES(?, ?)",[datetime.combine(datetime.strptime(date, '%Y-%m-%d'), time), schedule['name']])
                    except sq.IntegrityError:
                        pass
 
    DB.commit()

async def add_master(message: types.Message, master_data, kb):
    try:
        CURSOR.execute(f"""CREATE TABLE IF NOT EXISTS {master_data['name']}_schedule(
                       date DATETIME PRIMARY KEY,
                       master VARCHAR(30)
        )""")
        CURSOR.execute(f"INSERT INTO master VALUES(?, ?, ?, ?)", [master_data['name'], master_data['phone'], master_data['photo'], master_data['description']])
        DB.commit()
        return True
    except sq.IntegrityError:
        await message.answer(text='Master already exists!',
                             reply_markup=kb)
        return False

async def select_dates(name, count): #Поменял каунт на +6 так как буду выводить даты в пачке по 6. На входе каунт должен увеличиваться на +7, чтобы не отображать последнюю дату в прошлом выводе
    INFO = CURSOR.execute(f'SELECT (date, time) FROM {name}_schedule WHERE master == "{name}" LIMIT {count} OFFSET {count+6}')
    DB.commit()
    return INFO


async def check_date(date, name) -> bool:
    return date in CURSOR.execute(f'SELECT date FROM {name}_schedule WHERE master = "{name}"')


async def masters_list():
    INFO = CURSOR.execute("SELECT name FROM master")
    DB.commit()
    return INFO


async def insert_service(service, price, duration, name):
    CURSOR.execute("INSERT INTO service VALUES(?, ?, ?, ?)", [service, price, duration, name])
    DB.commit()


async def delete_date(dates, name):
    if len(dates) > 10:
        for year in range(datetime.strptime(dates.split(' - ')[0], '%Y-%m-%d').year, datetime.strptime(dates.split(' - ')[1], '%Y-%m-%d').year + 1, 1):
            for month in range(datetime.strptime(dates.split(' - ')[0], '%Y-%m-%d').month, datetime.strptime(dates.split(' - ')[1], '%Y-%m-%d').month + 1, 1):
                for day in range(datetime.strptime(dates.split(' - ')[0], '%Y-%m-%d').day, datetime.strptime(dates.split(' - ')[1], '%Y-%m-%d').day + 1, 1):
                    CURSOR.execute(f"DELETE FROM {name}_schedule WHERE strftime('%Y-%m-%d', date)=?", [str(datetime.strptime(f'{year}-{month}-{day}', '%Y-%m-%d').date())])
                    DB.commit()
    else:
        CURSOR.execute(f"DELETE FROM {name}_schedule WHERE strftime('%Y-%m-%d', date)=?", [dates])
        DB.commit()


async def delete_time(date, time, name):
    

    if len(date) > 10:
        for year in range(datetime.strptime(date.split(' - ')[0], '%Y-%m-%d').year, datetime.strptime(date.split(' - ')[1], '%Y-%m-%d').year + 1, 1):
            for month in range(datetime.strptime(date.split(' - ')[0], '%Y-%m-%d').month, datetime.strptime(date.split(' - ')[1], '%Y-%m-%d').month + 1, 1):
                for day in range(datetime.strptime(date.split(' - ')[0], '%Y-%m-%d').day, datetime.strptime(date.split(' - ')[1], '%Y-%m-%d').day + 1, 1):
                    time_to_del = list()
                    if len(time) > 5:
                        for hour in range(datetime.strptime(time.split(' - ')[0], '%H:%M').hour, datetime.strptime(time.split(' - ')[1], '%H:%M').hour + 1, 1):
                            for minute in range(0, 31, 30):
                                time_to_del.append(datetime.strptime(f'{year}-{month}-{day} {hour}:{minute}', '%Y-%m-%d %H:%M'))
                        if datetime.strptime(time.split(' - ')[0], '%H:%M').minute != 0 and datetime.strptime(time.split(' - ')[1], '%H:%M').minute != 0:
                            time_to_del.pop(0)
                        elif datetime.strptime(time.split(' - ')[0], '%H:%M').minute == 0 and datetime.strptime(time.split(' - ')[1], '%H:%M').minute == 0:
                            time_to_del.pop(-1)
                        elif datetime.strptime(time.split(' - ')[0], '%H:%M').minute != 0 and datetime.strptime(time.split(' - ')[1], '%H:%M').minute == 0:
                            time_to_del.pop(0)
                            time_to_del.pop(-1)

                    elif len(time) == 5 or len(time) == 4:
                        time_to_del.append(datetime.strptime(f'{year}-{month}-{day} {time}', '%Y-%m-%d %H:%M'))

                    

                    for item in time_to_del:
                        CURSOR.execute(f"DELETE FROM {name}_schedule WHERE strftime('%Y-%m-%d %H:%M:%S', date)=?", [item])
                        DB.commit()

    
    elif len(date) <= 10:
        if len(time) > 5:
            time_to_del = list()
            for hour in range(datetime.strptime(time.split(' - ')[0], '%H:%M').hour, datetime.strptime(time.split(' - ')[1], '%H:%M').hour + 1, 1):
                for minute in range(0, 31, 30):
                    time_to_del.append(datetime.strptime(f'{datetime.strptime(date.split(" - ")[0], "%Y-%m-%d").year}-{datetime.strptime(date.split(" - ")[0], "%Y-%m-%d").month}-{datetime.strptime(date.split(" - ")[0], "%Y-%m-%d").day} {hour}:{minute}', '%Y-%m-%d %H:%M'))

            if datetime.strptime(time.split(' - ')[0], '%H:%M').minute != 0 and datetime.strptime(time.split(' - ')[1], '%H:%M').minute != 0:
                time_to_del.pop(0)
            elif datetime.strptime(time.split(' - ')[0], '%H:%M').minute == 0 and datetime.strptime(time.split(' - ')[1], '%H:%M').minute == 0:
                time_to_del.pop(-1)
            elif datetime.strptime(time.split(' - ')[0], '%H:%M').minute != 0 and datetime.strptime(time.split(' - ')[1], '%H:%M').minute == 0:
                time_to_del.pop(0)
                time_to_del.pop(-1)

            for item in time_to_del:
                CURSOR.execute(f"DELETE FROM {name}_schedule WHERE strftime('%Y-%m-%d %H:%M:%S', date)=?", [item])
                DB.commit()

        elif len(time) == 5 or len(time) == 4:
            CURSOR.execute(f"DELETE FROM {name}_schedule WHERE strftime('%Y-%m-%d %H:%M:%S', date)=?", [f'{datetime.strptime(date.split(" - ")[0], "%Y-%m-%d")} {datetime.strptime(time.split, "%H:%M")}'])
            DB.commit()
            
async def format_check(date, time):
    try:
        datetime.strptime(date.split(' - ')[0], '%Y-%m-%d')
        datetime.strptime(time.split(' - ')[0], '%H:%M')
        if len(date) > 10:
            datetime.strptime(date.split(' - ')[1], '%Y-%m-%d')
        if len(time) > 5:
            datetime.strptime(time.split(' - ')[1], '%H:%M')
        return True
    except ValueError:
        print(date)
        return False

async def resign_master(name):
    CURSOR.execute("DELETE FROM service WHERE master_name=?", [name])
    CURSOR.execute("DELETE FROM master WHERE name=?", [name])
    CURSOR.execute(f"DROP TABLE {name}_schedule")

    DB.commit()


async def service_list(name):
    return list(CURSOR.execute(f"SELECT service FROM service WHERE master_name=?", [name]))


async def delete_service(service, name):
    CURSOR.execute("DELETE FROM service WHERE service=? AND master_name=?", [service, name])

async def avalibale_dates_list(name, count, year):
    try:
        if datetime.now().month < 10:
            return [day[0] for day in CURSOR.execute(f"SELECT DISTINCT(strftime('%d', date)) FROM {name}_schedule WHERE strftime('%m', date)=? AND date>=? AND strftime('%Y', date)=?", [f"0{count}", datetime.now().date(), f'{year}'])]
        else:
            return [day[0] for day in CURSOR.execute(f"SELECT DISTINCT(strftime('%d', date)) FROM {name}_schedule WHERE strftime('%m', date)=? AND date>=? AND strftime('%Y', date)=?", [count, datetime.now().date(), f'{year}'])]
    except ValueError:
        pass

async def get_service(name):
    return list(CURSOR.execute(f"SELECT service, price, duration FROM service where master_name=?", [name]))  


async def get_caption(name):
    return list(CURSOR.execute(f"SELECT description FROM master WHERE name=?", [name]))


async def get_photo(name):
    return list(CURSOR.execute(f"SELECT photo FROM master WHERE name=?", [name]))


async def get_time_list(data, name):
    if int(data.split('.')[1]) < 10:
        if int(data.split('.')[0]) == datetime.now().day and int(data.split('.')[1]) == datetime.now().month:
            return list(map(lambda x: x[0], CURSOR.execute(f"SELECT strftime('%H:%M', date) FROM {name}_schedule WHERE strftime('%m', date)=? AND strftime('%d', date)=? AND strftime('%H:%M', date) >= ?", [f"0{data.split('.')[1]}", data.split('.')[0], datetime.strftime(datetime.now(), '%H:%M')])))
        else:
            return list(map(lambda x: x[0], CURSOR.execute(f"SELECT strftime('%H:%M', date) FROM {name}_schedule WHERE strftime('%m', date)=? AND strftime('%d', date)=?", [f"0{data.split('.')[1]}", data.split('.')[0]])))
    else:
        if int(data.split('.')[0]) == datetime.now().day and int(data.split('.')[1]) == datetime.now().month:
            return list(map(lambda x: x[0], CURSOR.execute(f"SELECT strftime('%H:%M', date) FROM {name}_schedule WHERE strftime('%m', date)=? AND strftime('%d', date)=? AND strftime('%H:%M', date)>=?", [f"{data.split('.')[1]}", data.split('.')[0], datetime.strftime(datetime.now(), '%H:%M')])))
        else:
            return list(map(lambda x: x[0], CURSOR.execute(f"SELECT strftime('%H:%M', date) FROM {name}_schedule WHERE strftime('%m', date)=? AND strftime('%d', date)=?", [f"{data.split('.')[1]}", data.split('.')[0]])))


async def daily_notify(bot: Bot, chat_id: int):
    for master in [master[0] for master in CURSOR.execute("SELECT name FROM master")]:
        Master_data = list(CURSOR.execute("SELECT service, date, duration FROM book WHERE master=? AND strftime('%Y-%m-%d', date)=?", [master, datetime.now().date()]))
        stroka = ''
        for time in Master_data:
            stroka += f"{datetime.strptime(str(time[1]).split()[1][0:-3], '%H:%M').time()} - {datetime.strptime(str(timedelta(hours=int(time[1].split()[1].split(':')[0]), minutes=int(time[1].split()[1].split(':')[1])) + timedelta(hours=int(time[2].split(':')[0]), minutes=int(time[2].split(':')[1])))[0:-3], '%H:%M').time()} - {time[0]}\n" 
        await bot.send_message(chat_id=chat_id, text=f'{datetime.strftime(datetime.now().date(), "%d.%m")}\nMaster: {master} - {len(Master_data)} visitors\n{stroka}')

        #Сформировать сроку из дата начала - дата окончания - название \n


async def show_signs(id):
    return list(CURSOR.execute(f"SELECT service, date, order_id FROM book WHERE id=? AND date>=?", [id, datetime.now().date()]))
    


async def del_sign_db(order_id, user_id, bot: Bot, scheduler: AsyncIOScheduler):
    for x, y, z in CURSOR.execute(f"SELECT duration, date, master FROM book WHERE order_id=?", [order_id]):
        INFO = (datetime.strptime(x, '%H:%M:%S').time(), datetime.strptime(y, '%Y-%m-%d %H:%M:%S'), z)
    times_to_add = list()
    max_date = tuple(CURSOR.execute("SELECT MAX(date) FROM book WHERE id=?", [user_id]))[0][0]

    for hour in range(INFO[1].hour, INFO[1].hour + INFO[0].hour + 1, 1):
        for minute in range(0, 31, 30):
            times_to_add.append(time(hour=hour, minute=minute))

    if INFO[1].minute == 0 and INFO[0].minute == 0:
        times_to_add = times_to_add[0:-1]
    elif INFO[1].minute == 30:
        if INFO[0].minute == 0:
            times_to_add = times_to_add[1::]
        elif INFO[0].minute == 30:
            times_to_add = times_to_add[1::]
            times_to_add.append(time(hour=times_to_add[-1].hour+1))
    
    for elem in times_to_add:
        CURSOR.execute(f"INSERT INTO {INFO[2]}_schedule VALUES(?, ?)", [datetime.combine(INFO[1].date(), elem), INFO[2]])
        DB.commit()
    
    CURSOR.execute(f"DELETE FROM book WHERE order_id=?", [order_id])
    DB.commit()

    if max_date == tuple(CURSOR.execute(f"SELECT date FROM book WHERE order_id=?", [order_id]))[0][0] if len(tuple(CURSOR.execute(f"SELECT date FROM book WHERE order_id=?", [order_id]))) else 0:
        scheduler.add_job(send_notify, trigger='data', run_time=(datetime.strptime(CURSOR.execute("SELECT MAX(date) FROM book WHERE user_id=?", [user_id]), '%Y-%m-%d %H:%M:%S') + timedelta(weeks=3)), id=f"{user_id}_first", replace_existing=True)
        scheduler.add_job(send_notify, trigger='data', run_time=(datetime.strptime(CURSOR.execute("SELECT MAX(date) FROM book WHERE user_id=?", [user_id]), '%Y-%m-%d %H:%M:%S') + timedelta(weeks=5)), id=f"{user_id}_second", replace_existing=True)
    scheduler.remove_job(f'{order_id}_service')
    user_info = tuple(CURSOR.execute("SELECT name, phone FROM client WHERE user_id=?", (user_id, )))[0]
    for id in admins:
        await bot.send_message(chat_id=id, text=f'Client deleted sign\nName: {user_info[0]} Phone: {user_info[1]}')
    #Добавить удаление уведа о скором посещении услуги в любом случае - сверху админское сообщение


async def delete_orders():
    CURSOR.execute("DELETE FROM book WHERE strftime('%Y-%m-%d', date)<?", [datetime.now().date() - timedelta(weeks=4)])
    DB.commit()
