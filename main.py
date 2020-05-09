import telebot
import cherrypy
import psycopg2
from telebot import types
import datetime
import hashlib

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

conn = psycopg2.connect(dbname='adm', user='adm',
                    password='adm', host='127.0.0.1')

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
    print(message.text)
    with conn.cursor() as cur:
        try:
            id = int(message.chat.id)
            cur.execute('SELECT msg FROM users WHERE id = %s', [id])
            msg = cur.fetchone()[0]
            if id == message.chat.id and msg != None:
                bot.delete_message(message_id = msg, chat_id = id)
                msg = bot.send_message(id, "Меню", reply_markup = key_main())
                cur.execute('UPDATE users SET msg = %s WHERE id = %s', (int(msg.message_id), int(id)))
                conn.commit()
        except:
            msg = bot.send_message(message.chat.id, '''Приветствую тебя.
            Надоело выполнять ебанутые\
            приказы командиров (начальников)?\
            Заебали самолёты?\
            Живешь от зарплаты до зарплаты?\
            Не хочешь брать кредит на машину?\
            Тогда тебе к нам. С нами ты получишь стабильный заработок,\
            сидя дома и играя в доту, забудешь что такое кредиты и финансовые проблемы.\
            Жми \"Заработать\" и делай свои первые деньги.''', reply_markup = key_main())
            hash = hashlib.md5(str(id).encode())
            cur.execute("INSERT INTO users (id, name, date, msg, ref) VALUES (%s, %s, %s, %s, %s)",
            (int(message.chat.id), str(message.chat.last_name + ' ' + message.chat.first_name),
            datetime.datetime.today().strftime('%Y-%m-%d-%H.%M.%S'), int(msg.message_id), str(hash.hexdigest())))
            conn.commit()

@bot.message_handler(content_types=['text'])
def handler(message):
    with conn.cursor() as cur:
            id = int(message.chat.id)
            cur.execute('SELECT msg FROM users WHERE id = %s', [id])
            msg = cur.fetchone()[0]
            if id == message.chat.id and msg != None:
                bot.delete_message(message_id = msg, chat_id = id)
                if(message.text == '🤑 Заработать'):
                    msg = bot.send_message(id, "Выберите способ заработка", reply_markup = key_money())
                if(message.text == '👥 Партнеры'):
                    msg = bot.send_message(id, '''Приглашайте партнёров в бот и \
                    получайте за них деньги!\
                    \
                    Отправьте другу ссылку в телеграме:\
                    ''' + partners(id, 1) + '''\
                    \
                    300 руб. за каждого приглашенного Вами партнера\
                    Приглашённых пользователей: ''' + partners(id, 2), reply_markup = key_main())
                cur.execute('UPDATE users SET msg = %s WHERE id = %s', (int(msg.message_id), int(id)))
                conn.commit()

@bot.callback_query_handler(func = lambda call: True) #Приём CALL_BACK_DATA с кнопок
def callback_inline(call):
    print("callback")

def partners(id, func):
    with conn.cursor() as cur:
        if(func == 1):
            cur.execute('SELECT ref FROM users WHERE id = %s', [id])
            return 'https:/t.me/imaycash_bot?start=' + cur.fetchone()[0]
        if(func == 2):
            cur.execute('SELECT COUNT(id_me) FROM partners WHERE id_me = %s', [id])
            n = cur.fetchne()[0]
            return n + '''/nЗаработок: ''' + (200 * int(n))

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
