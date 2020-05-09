import telebot
import cherrypy
import psycopg2
from telebot import types

API_TOKEN = '1129280265:AAGcX5WBLwReXZOEbMHvLQpD-BoYnMhSyn0'
WEBHOOK_HOST = '138.68.22.231'
WEBHOOK_PORT = 80 #8443 80 88 443
WEBHOOK_LISTEN = '0.0.0.0'
WEBHOOK_SSL_CERT = '/home/tele/cert/cert.pem'
WEBHOOK_SSL_PRIV = '/home/tele/cert/pkey.key'
WEBHOOK_URL_BASE = 'https://' + str(WEBHOOK_HOST) + ':' + str(WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (API_TOKEN)

bot = telebot.TeleBot(API_TOKEN)

class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
           'content-type' in cherrypy.request.headers and \
           cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)
#begin

def key_main():
    keyboard = types.ReplyKeyboardMarkup(row_width = 2, resize_keyboard = True)
    btns = []
    btns.append(types.KeyboardButton('🤑 Заработать'))
    btns.append(types.KeyboardButton('👥 Партнеры'))
    btns.append(types.KeyboardButton('💰 Баланс'))
    btns.append(types.KeyboardButton('❔ Помощь'))
    keyboard.add(*btns)
    return keyboard

def key_money():
    keyboard = types.InlineKeyboardMarkup(row_width = 1)
    btns = []
    btns.append(types.InlineKeyboardButton('🗣 Пригласить друга, 200руб', callback_data = "say"))
    btns.append(types.InlineKeyboardButton('📌 Подписаться на канал, 100руб', callback_data = "follow"))
    btns.append(types.InlineKeyboardButton('👀 Посмотреть записи, 50руб', callback_data = "see"))
    keyboard.add(*btns)
    return keyboard

@bot.message_handler(commands = ['start'])  #При подключении к боту выкидывать MENU
def start(message):
    try:
        msg = int(open('msg_id' + str(message.chat.id)).read())
        bot.delete_message(message_id = msg, chat_id = message.chat.id)
    except:
        print("Сообщений не найдено")
    msg = bot.send_message(message.chat.id, "Приветствую тебя.\
    Надоело выполнять ебанутые\
    приказы командиров (начальников)?\
    Заебали самолёты?\
    Живешь от зарплаты до зарплаты?\
    Не хочешь брать кредит на машину?\
    Тогда тебе к нам. С нами ты получишь стабильный заработок,\
    сидя дома и играя в доту, забудешь что такое кредиты и финансовые проблемы.\
    Жми \"Заработать\" и делай свои первые деньги.", reply_markup = key_main())
    with open('msg_id' + str(message.chat.id), 'w') as f:
        f.write(str(msg.message_id))

@bot.message_handler(content_types=['text'])
def handler(message):
    try:
        msg = int(open('msg_id' + str(message.chat.id)).read())
        bot.delete_message(message_id = msg, chat_id = message.chat.id)
    except:
        print("Сообщений не найдено")
    if message.text == '🤑 Заработать':
        msg = bot.send_message(message.chat.id, "Выберите способ заработка", reply_markup = key_money())
        with open('msg_id' + str(message.chat.id), 'w') as f:
            f.write(str(msg.message_id))

@bot.callback_query_handler(func = lambda call: True) #Приём CALL_BACK_DATA с кнопок
def callback_inline(call):
    try:
        msg = int(open('msg_id' + str(call.message.chat.id)).read())
        bot.delete_message(message_id = msg, chat_id = call.message.chat.id)
    except:
        print("Сообщений не найдено ")
    if call.data == 'say':
        msg = bot.send_message(call.message.chat.id, "Приглашайте партнёров в бот и получайте за них \
        деньги!\n https://t.me/imaycash_bot \n 200руб за каждого приглашенного Вами партнера", reply_markup = key_main())
    if call.data == 'follow':
        follow(call.message.chat.id)
    if call.data == 'see':
        msg = bot.send_message(call.message.chat.id, "Вы просмотрели всю рекламу", reply_markup = key_main())
    with open('msg_id' + str(call.message.chat.id), 'w') as f:
        f.write(str(msg.message_id))

def follow(id):
    conn = psycopg2.connect(dbname='adm', user='adm',
                        password='adm', host='127.0.0.1')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM test')
    msg = bot.send_message(id, cursor.fetchone(), reply_markup = key_main())

#end
bot.remove_webhook()
bot.set_webhook(url = WEBHOOK_URL_BASE + WEBHOOK_URL_PATH, certificate = open(WEBHOOK_SSL_CERT, 'r'))

cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})

cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
