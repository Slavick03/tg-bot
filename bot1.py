import telebot
from telebot import types
import threading
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
EVENTS_FILE = 'events.json'

bot = telebot.TeleBot(BOT_TOKEN)

# Инициализация JSON файла
def init_storage():
    if not os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'events': [], 'last_id': 0}, f, ensure_ascii=False, indent=2)

def load_events():
    with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_events(data):
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

init_storage()

def return_to_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('➕ Добавить событие')
    btn2 = types.KeyboardButton('📋 Мои события')
    btn3 = types.KeyboardButton('🗑 Удалить событие')
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, '❌ Действие отменено', reply_markup=markup)

@bot.message_handler(commands=['start'])
def startBot(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('➕ Добавить событие')
    btn2 = types.KeyboardButton('📋 Мои события')
    btn3 = types.KeyboardButton('🗑 Удалить событие')
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id,
                    f'Привет, {message.from_user.first_name}! 👋\n\n'
                    'Я помогу тебе не забыть о важных событиях.\n\n'
                    'Выбери действие:',
                    reply_markup=markup)

@bot.message_handler(commands=['add'])
def add_event_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_cancel = types.KeyboardButton('❌ Отмена')
    markup.add(btn_cancel)
    bot.send_message(message.chat.id,
                    'Введи название события:',
                    reply_markup=markup)
    bot.register_next_step_handler(message, get_event_name)

def get_event_name(message):
    if message.text == '❌ Отмена':
        return_to_main_menu(message)
        return
    event_name = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_cancel = types.KeyboardButton('❌ Отмена')
    markup.add(btn_cancel)
    bot.send_message(message.chat.id, 'Введи описание события:', reply_markup=markup)
    bot.register_next_step_handler(message, get_event_description, event_name)

def get_event_description(message, event_name):
    if message.text == '❌ Отмена':
        return_to_main_menu(message)
        return
    description = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_cancel = types.KeyboardButton('❌ Отмена')
    markup.add(btn_cancel)
    bot.send_message(message.chat.id,
                    'Введи дату и время события в формате:\n'
                    'ДД.ММ.ГГГГ ЧЧ:ММ\n\n'
                    'Например: 25.05.2026 15:30',
                    reply_markup=markup)
    bot.register_next_step_handler(message, get_event_time, event_name, description)

def get_event_time(message, event_name, description):
    if message.text == '❌ Отмена':
        return_to_main_menu(message)
        return
    try:
        event_time_str = message.text
        event_time = datetime.strptime(event_time_str, '%d.%m.%Y %H:%M')

        if event_time < datetime.now():
            bot.send_message(message.chat.id, '❌ Нельзя создать событие в прошлом!')
            return

        data = load_events()
        data['last_id'] += 1

        new_event = {
            'id': data['last_id'],
            'user_id': message.from_user.id,
            'event_name': event_name,
            'description': description,
            'event_time': event_time.isoformat(),
            'notified': False,
            'created_at': datetime.now().isoformat()
        }

        data['events'].append(new_event)
        save_events(data)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('➕ Добавить событие')
        btn2 = types.KeyboardButton('📋 Мои события')
        btn3 = types.KeyboardButton('🗑 Удалить событие')
        markup.add(btn1, btn2, btn3)

        bot.send_message(message.chat.id,
                        f'✅ Событие создано!\n\n'
                        f'📌 {event_name}\n'
                        f'📝 {description}\n'
                        f'🕐 {event_time_str}\n\n'
                        f'Я напомню тебе в указанное время!',
                        reply_markup=markup)
    except ValueError:
        bot.send_message(message.chat.id,
                        '❌ Неверный формат даты!\n'
                        'Используй формат: ДД.ММ.ГГГГ ЧЧ:ММ')

@bot.message_handler(commands=['list'])
def list_events(message):
    data = load_events()
    user_events = [e for e in data['events']
                   if e['user_id'] == message.from_user.id and not e['notified']]

    user_events.sort(key=lambda x: x['event_time'])

    if not user_events:
        bot.send_message(message.chat.id, '📭 У тебя пока нет запланированных событий.')
        return

    response = '📋 Твои события:\n\n'
    for event in user_events:
        event_time = datetime.fromisoformat(event['event_time'])
        response += f'🆔 {event["id"]}\n'
        response += f'📌 {event["event_name"]}\n'
        response += f'📝 {event["description"]}\n'
        response += f'🕐 {event_time.strftime("%d.%m.%Y %H:%M")}\n'
        response += '─' * 30 + '\n\n'

    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['delete'])
def delete_event_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_cancel = types.KeyboardButton('❌ Отмена')
    markup.add(btn_cancel)
    bot.send_message(message.chat.id,
                    'Введи ID события для удаления:\n'
                    '(Посмотреть ID можно командой /list)',
                    reply_markup=markup)
    bot.register_next_step_handler(message, delete_event)

def delete_event(message):
    if message.text == '❌ Отмена':
        return_to_main_menu(message)
        return
    try:
        event_id = int(message.text)
        data = load_events()

        initial_count = len(data['events'])
        data['events'] = [e for e in data['events']
                         if not (e['id'] == event_id and e['user_id'] == message.from_user.id)]

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('➕ Добавить событие')
        btn2 = types.KeyboardButton('📋 Мои события')
        btn3 = types.KeyboardButton('🗑 Удалить событие')
        markup.add(btn1, btn2, btn3)

        if len(data['events']) < initial_count:
            save_events(data)
            bot.send_message(message.chat.id, '✅ Событие удалено!', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, '❌ Событие не найдено!', reply_markup=markup)
    except ValueError:
        bot.send_message(message.chat.id, '❌ Неверный ID!')

@bot.message_handler()
def get_info(message):
    if message.text == '➕ Добавить событие':
        add_event_start(message)
    elif message.text == '📋 Мои события':
        list_events(message)
    elif message.text == '🗑 Удалить событие':
        delete_event_start(message)
    elif message.text.lower() == 'привет':
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}! 👋')
    elif message.text.lower() == 'id':
        bot.reply_to(message, f'ID: {message.from_user.id}')
    else:
        bot.send_message(message.chat.id,
                        'Используй кнопки меню или команды:\n'
                        '/add - добавить событие\n'
                        '/list - список событий\n'
                        '/delete - удалить событие')

def check_notifications():
    while True:
        try:
            data = load_events()
            current_time = datetime.now()
            events_to_remove = []

            for event in data['events']:
                if not event['notified']:
                    event_time = datetime.fromisoformat(event['event_time'])

                    if current_time >= event_time:
                        try:
                            bot.send_message(event['user_id'],
                                           f'⏰ НАПОМИНАНИЕ!\n\n'
                                           f'📌 {event["event_name"]}\n'
                                           f'📝 {event["description"]}\n'
                                           f'🕐 {event_time.strftime("%d.%m.%Y %H:%M")}')

                            events_to_remove.append(event['id'])
                        except Exception as e:
                            print(f'Ошибка отправки уведомления: {e}')

            # Удаляем события после отправки уведомлений
            if events_to_remove:
                data['events'] = [e for e in data['events'] if e['id'] not in events_to_remove]
                save_events(data)
                print(f'Удалено событий: {len(events_to_remove)}')

            time.sleep(30)
        except Exception as e:
            print(f'Ошибка в потоке уведомлений: {e}')
            time.sleep(30)

print('Bot started')

notification_thread = threading.Thread(target=check_notifications, daemon=True)
notification_thread.start()

bot.infinity_polling()
