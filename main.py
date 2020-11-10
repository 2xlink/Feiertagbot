import sys
import os
import time
import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
from datetime import datetime
import json
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
	# 	cursor.execute('''INSERT INTO users(id, state, hour, minute)
	# 	                  VALUES(?,?,?,?)''', (chat_id, state, hour, minute))
	# else:
	# 	cursor.execute('''UPDATE users SET state = ?, hour = ?, minute = ?
	# 		              WHERE id = ? ''', (state, hour, minute, chat_id))
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


def handle_notification(user):
	chat_id = user[0]
	state = user[1]

	with open(scriptPath + "/data/" + state) as json_file:
		json_parsed = json.load(json_file)
		for newday in (json_parsed['daten']):
			# pprint(newday)
			# check if tomorrow is not a sunday
			if (datetime.today().weekday()) == 6: return
			if (datetime.today().weekday() + 1) != 6:
				checktime = time.time()+24*60*60 # tomorrow
				sunday = False
			else:
				checktime = time.time()+48*60*60 # day after tomorrow
				sunday = True

			if ((checktime > newday['beginn']) and (checktime < newday['ende'])):
				if not sunday:
					message = 'Morgen ist ' + newday['title'] + '!' + extraMessage
				else:
					message = 'Übermorgen ist ' + newday['title'] + '!' + extraMessage

				try:
					bot.sendMessage(chat_id, message)
					print("Sent a message for " + str(chat_id) + ": " + message)
				except Exception as e:
					print("Error while sending message!")
					print(e)


def land_lang_zu_kurz(land_lang):
	switcher = {
		"Baden-Württemberg": "BW",
		"Bayern": "BY",
		"Berlin": "BE",
		"Brandenburg": "BB",
		"Bremen": "HB",
		"Hamburg": "HH",
		"Hessen": "HE",
		"Mecklenburg-Vorpommern": "MV",
		"Niedersachsen": "NI",
		"Nordrhein-Westfalen": "NW",
		"Rheinland-Pfalz": "RP",
		"Saarland": "SL",
		"Sachsen": "SN",
		"Sachsen-Anhalt": "ST",
		"Schleswig-Holstein": "SH",
		"Thüringen": "TH"
	}
	return switcher.get(land_lang, "nothing")


def on_chat_message(msg):
	content_type, chat_type, chat_id = telepot.glance(msg)
	print("Got a new message: ")
	pprint(msg)
	if msg['text'] == "/start":
		keyboard = InlineKeyboardMarkup(inline_keyboard=[
			[InlineKeyboardButton(text='Baden-Württemberg', callback_data='Baden-Württemberg')],  
			[InlineKeyboardButton(text='Bayern', callback_data='Bayern')],     
			[InlineKeyboardButton(text='Berlin', callback_data='Berlin')],     
			[InlineKeyboardButton(text='Brandenburg', callback_data='Brandenburg')],    
			[InlineKeyboardButton(text='Bremen', callback_data='Bremen')],     
			[InlineKeyboardButton(text='Hamburg', callback_data='Hamburg')],    
			[InlineKeyboardButton(text='Hessen', callback_data='Hessen')],     
			[InlineKeyboardButton(text='Mecklenburg-Vorpommern', callback_data='Mecklenburg-Vorpommern')],     
			[InlineKeyboardButton(text='Niedersachsen', callback_data='Niedersachsen')],  
			[InlineKeyboardButton(text='Nordrhein-Westfalen', callback_data='Nordrhein-Westfalen')],    
			[InlineKeyboardButton(text='Rheinland-Pfalz', callback_data='Rheinland-Pfalz')],    
			[InlineKeyboardButton(text='Saarland', callback_data='Saarland')],   
			[InlineKeyboardButton(text='Sachsen', callback_data='Sachsen')],    
			[InlineKeyboardButton(text='Sachsen-Anhalt', callback_data='Sachsen-Anhalt')],     
			[InlineKeyboardButton(text='Schleswig-Holstein', callback_data='Schleswig-Holstein')],     
			[InlineKeyboardButton(text='Thüringen', callback_data='Thüringen')],  
				   ])

		bot.sendMessage(chat_id, 'Wähle dein Bundesland', reply_markup=keyboard)
		return

	if msg['text'][:5] == "/zeit" or msg['text'][:5] == "/Zeit":
		time_s = msg['text'][6:]
		try:
			date = datetime.strptime(time_s, "%H:%M")
		except ValueError:
			bot.sendMessage(chat_id, 'Bitte gib deine Zeit in Form von "/zeit hh:mm" ein\
				\nZum Beispiel /zeit 14:30')
			return
		insert_into_db(chat_id, None, date.hour, date.minute)
		bot.sendMessage(chat_id, "Deine Weckzeit ist jetzt " + time_s)
		return

	if msg['text'][:5] == "/info" or msg['text'][:5] == "/Info":
		bot.sendMessage(chat_id, "Ich wurde von @linklink erschaffen, falls ich helfen konnte darfst du natürlich \
gerne einen 👍 da lassen 😉\n\n\
Meinen Sourcecode findet ihr unter https://github.com/2xlink/Feiertagbot. Schönen Tag noch 👋")

def on_callback_query(msg):
	query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
	print('Callback Query:', query_id, from_id, query_data)

	land_kurz = land_lang_zu_kurz(query_data)

	if land_kurz == "nothing":
		bot.sendMessage(from_id, "Bundesland nicht gefunden.\n\
			Bitte sende erneut eine Nachricht um das Menu aufzurufen.")
		land_kurz = "SN"

	insert_into_db(from_id, land_kurz, None, None)

	# bot.answerCallbackQuery(query_id, text='Dein Bundesland ist jetzt: ' + query_data)
	bot.sendMessage(from_id, text='Dein Bundesland ist jetzt: ' + 
		query_data + '\nIch benachrichtige dich wenn ein Feiertag naht!\n' +
		'Du kannst übrigens deine Alarmzeit einstellen, z.B. /zeit 14:30\n' + extraMessage)


if __name__ == "__main__":
    
    TOKEN = sys.argv[1]
    bot = telepot.Bot(TOKEN)
    extraMessage = ""

    bot.message_loop({'chat': on_chat_message,
				  'callback_query': on_callback_query})
    print('Listening ...')

    while 1:
        users = get_all_from_db()
        for user in users:
            hour = user[2]
            minute = user[3]

            if datetime.now().time().hour == hour \
                and datetime.now().time().minute == minute:
                handle_notification(user) 

        time.sleep(60)
