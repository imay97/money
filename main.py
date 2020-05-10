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
    if message.text[7:] != '':
        print(message.text[7:])
        with conn.cursor() as cur:
            try:
                cur.execute('SELECT id_me FROM partners WHERE id_partners = %s', (message.chat.id,))
                if cur.fetchone()[0] != None:
                    cur.execute('SELECT id FROM users WHERE ref = %s', (message.text[7:],))
                    bot.send_message(cur.fetchone()[0], "Партнёр перешёл по вашей ссылке", reply_markup = key_main())
                    cur.execute('UPDATE users SET balance = balance + 200 WHERE id = %s', (cur.fetchone()[0]))
                    cur.execute('INSERT INTO partners (id_me, id_partners) VALUES (%s, %s)', (cur.fetchone()[0], message.chat.id))
                    conn.commit()
            except:
                print('Партнёр уже приглашен')
    else:
        with conn.cursor() as cur:
                id = message.chat.id
                try:
                    cur.execute('SELECT id FROM users WHERE id = %s', (id,))
                except:
                    conn.rollback()
                    print('Откат транзакции')
                try:
                    if id == cur.fetchone()[0]:
                        bot.send_message(id, "Меню", reply_markup = key_main())
                except:
                        bot.send_message(message.chat.id, 'Привет. Я бот для зарабатывания денег.', reply_markup = key_main())
                        hash = hashlib.md5(str(id).encode())
                        name = message.chat.last_name + ' ' + message.chat.first_name
                        date = datetime.datetime.today().strftime('%Y-%m-%d-%H.%M.%S')
                        try:
                            cur.execute('INSERT INTO users (id, name, date, ref, balance) VALUES (%s, %s, %s, %s, 0)', (id, name, date, str(hash.hexdigest())))
                            conn.commit()
                        except:
                            conn.rollback()
                            print('Откат. Пользователь не записан')

@bot.message_handler(content_types=['text'])
def handler(message):
    with conn.cursor() as cur:
        id = int(message.chat.id)
        if(message.text == '🤑 Заработать'):
            bot.send_message(id, "Выберите способ заработка", reply_markup = key_money())
        if(message.text == '👥 Партнеры'):
            bot.send_message(id, 'Приглашайте партнёров в бот и \
            получайте за них деньги!\
            \
            Отправьте другу ссылку в телеграме: \
            ' + partners(id, 1) + '\
            \
            200 руб. за каждого приглашенного Вами партнера\
            Приглашённых пользователей: ' + partners(id, 2), reply_markup = key_main())
        if(message.text == '❔ Помощь'):
            bot.send_message(id, "В этом боте очень простая система: ♻️каналы спонсоров платят боту за рекламу, а бот платит тебе за подписки на эти каналы!\
Выводить деньги из бота можно на: Сбербанк, Qiwi, ЯДеньги, WebMoney и др.\
\
📣Свой отзыв пиши мне: @flexone", reply_markup = key_main())
        if(message.text == '💰 Баланс'):
            cur.execute('SELECT balance FROM users WHERE id = %s', (id,))
            bot.send_message(id, "Ваш баланс: " + str(cur.fetchone()[0]) + " руб\n\
Минимальная сумма вывода: 3000 руб.", reply_markup = key_main())

@bot.callback_query_handler(func = lambda call: True) #Приём CALL_BACK_DATA с кнопок
def callback_inline(call):
    print("callback")

def partners(id, func):
    with conn.cursor() as cur:
        try:
            if(func == 1):
                cur.execute('SELECT ref FROM users WHERE id = %s', (id,))
                return 'https://t.me/imaycash_bot?start=' + cur.fetchone()[0]
            if(func == 2):
                cur.execute('SELECT COUNT(id_partners) FROM partners WHERE id_me = %s', (id,))
                n = cur.fetchone()[0]
                return str(n) + '\nЗаработок: ' + str(200 * int(n))
        except:
            return 'None'

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
