import telebot
import cherrypy
import sqlite3
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

@bot.message_handler(commands = ['start'])  #При подключении к боту выкидывать MENU
def start(message):
    msg = int(open('page_' + str(message.chat.id)).read())
    bot.delete_message(message_id = msg, chat_id = message.chat.id)
    keyboard = types.InlineKeyboardMarkup(row_width = 2)
    btns = []
    btns.append(types.InlineKeyboardButton(text = '🤑 Заработать', callback_data = 'work'))
    btns.append(types.InlineKeyboardButton(text = '👥 Партнеры', callback_data = 'partner'))
    btns.append(types.InlineKeyboardButton(text = '💰 Баланс', callback_data = 'money'))
    btns.append(types.InlineKeyboardButton(text = '❔ Помощь', callback_data = 'help'))
    keyboard.add(*btns)
    msg = bot.send_message(message.chat.id, "Привет", reply_markup = keyboard)
    with open('msg_id' + str(message.chat.id), 'w') as f:
		f.write(str(msg.message_id))

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
