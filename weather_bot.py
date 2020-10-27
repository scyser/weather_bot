from telebot import types, TeleBot
import requests
from datetime import datetime
from api_tokens import token_bot, token_weather

class MyTeleBot(TeleBot):
    """This class extands class TeleBot from lib telebot"""

    def __init__(self, token, parse_mode=None, threaded=True, skip_pending=False, num_threads=2, next_step_backend=None, reply_backend=None):
        """Adding dictionary for keeping last location"""

        TeleBot.__init__(self, token, parse_mode=None, threaded=True, skip_pending=False, num_threads=2, next_step_backend=None, reply_backend=None)
        self.geo_dict = {}

bot = MyTeleBot(token_bot, parse_mode=None)
api_key = token_weather

def keyboard_create():
    """Creating inline keyboard and returning it"""

    keyboard = types.InlineKeyboardMarkup()

    weather_now = types.InlineKeyboardButton(text='Cейчас', callback_data='now')
    weather_full = types.InlineKeyboardButton(text='Cутки', callback_data='day')
    weather_three = types.InlineKeyboardButton(text='Три дня', callback_data='three_days')
    delete_geo = types.InlineKeyboardButton(text='Удалить текущее местоположение', callback_data='delete_geo')

    keyboard.row(weather_now, weather_full, weather_three)
    keyboard.row(delete_geo)
    return keyboard

def button_create():
    """Creating reply button for sending location and returning it"""

    markup = types.ReplyKeyboardMarkup()
    send_geo = types.KeyboardButton('Отправить геопозицию', request_location=True)
    markup.add(send_geo)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Start/help hint"""

    bot.reply_to(message, 'Привет, это погодный бот! Отправь мне геолокацию!')


@bot.message_handler(content_types=['text'])
def send_text(message):
    """Handling text messages and replying"""

    if message.text.lower() in ['привет', 'hi', 'yo', 'йоу', 'йо', 'хай', 'hello']:
        bot.send_message(message.chat.id, f'{message.text.title()}, {message.chat.first_name}!')
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAMZX4xI4pYCSSzxDUkMStyk2ICOkuwAAtkHAAKMLf0HUpA0FAia114bBA')

    elif message.text.lower() in ['пока', 'bye', 'bb', 'goodbye', 'прощай', 'удачи']:
        bot.send_message(message.chat.id, f'{message.text.title()}, {message.chat.first_name}!')

    else:
        markup = button_create()
        bot.send_message(message.chat.id, 'Отправь мне свою геопозицию!', reply_markup=markup)


@bot.message_handler(content_types=['location'])
def receive_location(message):
    """Handling location, creating inline keyboard"""

    bot.geo_dict[str(message.chat.id)] = [message.location.latitude, message.location.longitude]

    keyboard = keyboard_create()

    bot.send_message(message.chat.id, "Выбери прогноз погоды:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def send_weather(call):
    """Handling calls of inline keyboard"""

    DAYS_WEEK = {
    '1': 'Понедельник',
    '2': 'Вторник',
    '3': 'Среда',
    '4': 'Четверг',
    '5': 'Пятница',
    '6': 'Суббота',
    '7': 'Воскресенье'
    }

    if call.data == 'now':
        if str(call.message.chat.id) in bot.geo_dict:
            params = {'lat': bot.geo_dict[str(call.message.chat.id)][0], 'lon': bot.geo_dict[str(call.message.chat.id)][1], 'lang': 'ru', 'appid': api_key}
            response = requests.get('https://api.openweathermap.org/data/2.5/weather', params=params)
            answer = response.json()
            temp = round(answer['main']['temp'] - 273.15, 2)
            feel_temp = round(answer['main']['feels_like'] - 273.15, 2)
            description = answer['weather'][0]['description'].capitalize()
            weather_mess = f'Погода сейчас\n{description}\nТемпература: {temp}\N{DEGREE SIGN}C\nОщущается как: {feel_temp}\N{DEGREE SIGN}C'
            bot.send_message(call.message.chat.id, weather_mess)

            keyboard = keyboard_create()
            bot.send_message(call.message.chat.id, "Выбери прогноз погоды:", reply_markup=keyboard)

        else:
            markup = button_create()
            bot.send_message(call.message.chat.id, 'Отправь мне свою геопозицию!', reply_markup=markup)

    elif call.data == 'day':
        if str(call.message.chat.id) in bot.geo_dict:
            params = {'lat': bot.geo_dict[str(call.message.chat.id)][0], 'lon': bot.geo_dict[str(call.message.chat.id)][1],'lang': 'ru', 'appid': api_key}
            response = requests.get('https://api.openweathermap.org/data/2.5/forecast', params=params)
            answer = response.json()
            weather_mess = 'Погода за сутки\n'

            for data in answer['list'][:8]:
                description = data['weather'][0]['description'].capitalize()
                weather_mess += str(datetime.time(datetime.fromtimestamp(data['dt']))) + '\n'
                temp = round(data['main']['temp'] - 273.15, 2)
                weather_mess += description + '\n'
                weather_mess += f'Температура: {temp}\N{DEGREE SIGN}C\n'
                weather_mess += '\n'
            bot.send_message(call.message.chat.id, weather_mess)
            
            keyboard = keyboard_create()
            bot.send_message(call.message.chat.id, "Выбери прогноз погоды:", reply_markup=keyboard)

        else:
            markup = button_create()
            bot.send_message(call.message.chat.id, 'Отправь мне свою геопозицию!', reply_markup=markup)

    elif call.data == 'three_days':
        if str(call.message.chat.id) in bot.geo_dict:
            params = {'lat': bot.geo_dict[str(call.message.chat.id)][0], 'lon': bot.geo_dict[str(call.message.chat.id)][1],'lang': 'ru', 'appid': api_key}
            response = requests.get('https://api.openweathermap.org/data/2.5/forecast', params=params)
            answer = response.json()
            weather_mess = 'Погода за три дня\n\n'

            day = datetime.isoweekday(datetime.fromtimestamp(answer['list'][0]['dt']))-1

            for data in answer['list'][:24]:

                if day != datetime.isoweekday(datetime.fromtimestamp(data['dt'])):
                    day += 1
                    if day > 7:
                        day = 1
                    weather_mess +=  '*' + DAYS_WEEK[str(day)] + '*' + '\n'

                description = data['weather'][0]['description'].capitalize()
                weather_mess += str(datetime.time(datetime.fromtimestamp(data['dt']))) + '\n'
                weather_mess += description + '\n'
                temp = round(data['main']['temp'] - 273.15, 2)
                weather_mess += f'Температура: {temp}\N{DEGREE SIGN}C\n'
                weather_mess += '\n'
            bot.send_message(call.message.chat.id, weather_mess, parse_mode='Markdown')

            keyboard = keyboard_create()
            bot.send_message(call.message.chat.id, "Выбери прогноз погоды:", reply_markup=keyboard)

        else:
            markup = button_create()
            bot.send_message(call.message.chat.id, 'Отправь мне свою геопозицию!', reply_markup=markup)

    elif call.data == 'delete_geo':
        try:
            bot.geo_dict.pop(str(call.message.chat.id))
        except Exception as e:
            print(e)
            



bot.polling()

