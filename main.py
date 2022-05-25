import sys
import os
import time
import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import datetime
import json
import random
from pprint import pprint

def getScriptPath():
        return os.path.dirname(os.path.realpath(sys.argv[0]))

scriptPath = getScriptPath()

def init_db(): # Usually does not need to be called anywhere
    db = sqlite3.connect(scriptPath + '/data/db.sqlite')
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE users(id INTEGER PRIMARY KEY, state TEXT, hour INTEGER, minute INTEGER)
    ''')
    db.commit()
    db.close()


def insert_into_db(chat_id, state, hour, minute):
    db = sqlite3.connect(scriptPath + '/data/db.sqlite')
    cursor = db.cursor()
    cursor.execute('''SELECT * FROM users WHERE id = ? ''', (chat_id,)); 
    user = cursor.fetchall()

    if state == None:
        if user == []: # User does not exist in DB yet
            cursor.execute('''INSERT INTO users(id, state, hour, minute)
                              VALUES(?,?,?,?)''', (chat_id, "SN", hour, minute))
        else:
            cursor.execute('''UPDATE users SET hour = ?, minute = ?
                              WHERE id = ? ''', (hour, minute, chat_id))

    elif hour == None or minute == None:
        if user == []:
            cursor.execute('''INSERT INTO users(id, state, hour, minute)
                              VALUES(?,?,?,?)''', (chat_id, state, 17, 00))
        else:
            cursor.execute('''UPDATE users SET state = ?
                              WHERE id = ? ''', (state, chat_id))

    else: raise ValueError("State and hour and minute is not None in insert_into_db")

    # if user == []:
    #   cursor.execute('''INSERT INTO users(id, state, hour, minute)
    #                     VALUES(?,?,?,?)''', (chat_id, state, hour, minute))
    # else:
    #   cursor.execute('''UPDATE users SET state = ?, hour = ?, minute = ?
    #                     WHERE id = ? ''', (state, hour, minute, chat_id))
    db.commit()
    db.close()


def get_all_from_db():
    db = sqlite3.connect(scriptPath + '/data/db.sqlite')
    cursor = db.cursor()
    cursor.execute('''SELECT * FROM users'''); 
    user = cursor.fetchall()
    db.commit()
    db.close()
    return user;


def handle_notification(user, global_holidays):
    chat_id = user[0]
    state = user[1]

    today = datetime.datetime.today().date()
    
    # Is today saturday?
    is_saturday = today.weekday() == 5

    if not is_saturday:
        check_date = today + datetime.timedelta(days = 1)
    else:
        check_date = today + datetime.timedelta(days = 2)

    for state_holiday in global_holidays.get(state).items():
        holiday_name = state_holiday[0]
        holiday_date_unparsed = state_holiday[1].get("datum")
        holiday_date = datetime.datetime.strptime(holiday_date_unparsed, "%Y-%m-%d").date()

        if check_date == holiday_date:
            if not is_saturday:
                message = 'Morgen ist ' + holiday_name + '!' + extraMessage
            else:
                message = 'Übermorgen ist ' + holiday_name + '!' + extraMessage

            try:
                bot.sendMessage(chat_id, message)
                print("Sent a message for " + str(chat_id) + ": " + message)
            except Exception as e:
                print("Error while sending message!")
                print(e)

def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    print("Got a new message: ")
    pprint(msg)

    if "text" not in msg:
        # Seems to be some kind of organizational message
        return

    if msg['text'][:6] == "/start":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Baden-Württemberg', callback_data='BW')],
            [InlineKeyboardButton(text='Bayern', callback_data='BY')],
            [InlineKeyboardButton(text='Berlin', callback_data='BE')],
            [InlineKeyboardButton(text='Brandenburg', callback_data='BB')],
            [InlineKeyboardButton(text='Bremen', callback_data='HB')],
            [InlineKeyboardButton(text='Hamburg', callback_data='HH')],
            [InlineKeyboardButton(text='Hessen', callback_data='HE')],
            [InlineKeyboardButton(text='Mecklenburg-Vorpommern', callback_data='MV')],
            [InlineKeyboardButton(text='Niedersachsen', callback_data='NI')],
            [InlineKeyboardButton(text='Nordrhein-Westfalen', callback_data='NW')],
            [InlineKeyboardButton(text='Rheinland-Pfalz', callback_data='RP')],
            [InlineKeyboardButton(text='Saarland', callback_data='SL')],
            [InlineKeyboardButton(text='Sachsen', callback_data='SN')],
            [InlineKeyboardButton(text='Sachsen-Anhalt', callback_data='ST')],
            [InlineKeyboardButton(text='Schleswig-Holstein', callback_data='SH')],
            [InlineKeyboardButton(text='Thüringen', callback_data='TH')],
                   ])

        bot.sendMessage(chat_id, 'Wähle dein Bundesland', reply_markup=keyboard)
        return

    elif msg['text'][:5] == "/zeit" or msg['text'][:5] == "/Zeit":
        time_s = msg['text'][6:]
        try:
            date = datetime.datetime.strptime(time_s, "%H:%M")
        except ValueError:
            bot.sendMessage(chat_id, 'Bitte gib deine Zeit in Form von "/zeit hh:mm" ein\
                \nZum Beispiel /zeit 14:30')
            return
        insert_into_db(chat_id, None, date.hour, date.minute)
        bot.sendMessage(chat_id, "Deine Weckzeit ist jetzt " + time_s)
        return

    elif msg['text'][:5] == "/info" or msg['text'][:5] == "/Info":
        bot.sendMessage(chat_id, "Ich wurde von @linklink erschaffen, falls ich hilfreich war darfst du natürlich \
gerne einen ⭐ da lassen 😉\n\n\
📜 Sourcecode 👉 https://github.com/2xlink/Feiertagbot")

    else:
        bot.sendMessage(chat_id, random.choice(["?", "What?", "何?", "¿Que?", "Entschuldigung, wie bitte?"]))

def on_callback_query(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    print('Callback Query:', query_id, from_id, query_data)

    allowed_states = ["BW", "BY", "BE", "BB", "HB", "HH", "HE", "MV", "NI", "NW", "RP", "SL", "SN", "ST", "SH", "TH"]

    if query_data not in allowed_states:
        bot.sendMessage(from_id, "Bundesland nicht gefunden.\n\
            Bitte sende erneut eine Nachricht um das Menu aufzurufen.")
        query_data = "SN"

    else:
        insert_into_db(from_id, query_data, None, None)
        bot.sendMessage(from_id, text='Dein Bundesland ist jetzt: ' + 
            query_data + '\nIch benachrichtige dich wenn ein Feiertag naht!\n' +
            'Du kannst übrigens deine Alarmzeit einstellen, z.B. /zeit 14:30\n' + extraMessage)


if __name__ == "__main__":
    
    TOKEN = sys.argv[1]
    bot = telepot.Bot(TOKEN)
    extraMessage = ""

    with open(scriptPath + f"/data/holidays-{datetime.datetime.today().year}.json") as json_file:
        holidays = json.load(json_file)

        bot.message_loop({'chat': on_chat_message,
                      'callback_query': on_callback_query})
        print('Listening ...')

        while 1:
            users = get_all_from_db()
            for user in users:
                hour = user[2]
                minute = user[3]

                now = datetime.datetime.now().time()

                if now.hour == hour and now.minute == minute:
                    handle_notification(user, holidays) 

            time.sleep(60)
