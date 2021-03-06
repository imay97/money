import telebot
import cherrypy
import psycopg2
from telebot import types
import datetime
import hashlib
import dropbox
import sys
sys.path.append("/home/tele/money/")
from dbx import *
from tlg import *

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
dbx = dropbox.Dropbox(dbx_token)

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
    btns.append(types.InlineKeyboardButton('📱 Меню', callback_data = "ok"))
    keyboard.add(*btns)
    return keyboard

def key_admin():
    keyboard = types.InlineKeyboardMarkup()
    btns = []
    btns1 = []
    btns2 = []
    btns.append(types.InlineKeyboardButton('Статистика', callback_data = "statistic_qsxcdlewgfwefwfafmag"))
    btns.append(types.InlineKeyboardButton('Рассылка', callback_data = "wefkbamklcsdfdsfhbffwca"))
    btns1.append(types.InlineKeyboardButton('Задания', callback_data = "uhbergubidvskmcxrnladfsbfgb"))
    btns1.append(types.InlineKeyboardButton('Рекламная рефералка', callback_data = "123g278hgui34tmdsknladfsbfgb"))
    btns2.append(types.InlineKeyboardButton('Выход', callback_data = "ok"))
    keyboard.add(*btns)
    keyboard.add(*btns1)
    keyboard.add(*btns2)
    return keyboard

def key_exit():
    keyboard = types.InlineKeyboardMarkup()
    btns = []
    btns.append(types.InlineKeyboardButton('Меню', callback_data = "ok"))
    keyboard.add(*btns)
    return keyboard

def key_exit_admin():
    keyboard = types.InlineKeyboardMarkup()
    btns = []
    btns.append(types.InlineKeyboardButton('Меню', callback_data = "ok_admin"))
    keyboard.add(*btns)
    return keyboard

def key_send_admin():
    keyboard = types.InlineKeyboardMarkup()
    btns = []
    btns.append(types.InlineKeyboardButton('Отправить', callback_data = "send_post"))
    keyboard.add(*btns)
    return keyboard

def key_send_video_admin():
    keyboard = types.InlineKeyboardMarkup()
    btns = []
    btns.append(types.InlineKeyboardButton('Отправить', callback_data = "send_video_post"))
    keyboard.add(*btns)
    return keyboard

def partners(id, func):
    with conn.cursor() as cur:
        cur.execute('UPDATE users SET active = %s WHERE id = %s', (datetime.datetime.today().strftime('%Y-%m-%d'), id))
        conn.commit()
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

def mailing(id):
    send('Отправльте текст. Если текст не нужен, то отправьте \'!\'', key_exit_admin(), id)
    with conn.cursor() as cur:
        cur.execute('UPDATE admins SET mod = 1')
        conn.commit()

def mailing_text(id, text):
    if text != '!':
        with open('/home/tele/money/content/text', 'w') as f:
            f.write(text)
        send('Отправльте картинку, видео или стик. Если этого не требуется, то отправьте \'!\'', key_exit_admin(), id)
    with conn.cursor() as cur:
        cur.execute('UPDATE admins SET mod = 2')
        conn.commit()

def send(text, markup, id):
    with conn.cursor() as cur:
        cur.execute('SELECT msg FROM users WHERE id = %s', (id,))
        if bool(cur.rowcount):
            try:
                bot.delete_message(message_id = cur.fetchone()[0], chat_id = id)
            except:
                print('Can\'t delete message')
        if markup != None:
            msg = bot.send_message(id, text, reply_markup = markup, parse_mode="HTML")
            cur.execute('UPDATE users SET msg = %s WHERE id = %s', (msg.message_id, id))
            conn.commit()
            return msg.message_id
        else:
            msg = bot.send_message(id, text, parse_mode="HTML")
            cur.execute('UPDATE users SET msg = %s WHERE id = %s', (msg.message_id, id))
            conn.commit()
            return msg.message_id
#--------------------------------------------------обработчики------------------------------------------------------------
@bot.message_handler(content_types=['document'])
def handle_docs_photo(message):
    with conn.cursor() as cur:
        cur.execute('SELECT mod FROM admins WHERE id = %s', (message.chat.id,))
        if bool(cur.rowcount):
            mod = cur.fetchone()[0]
            if mod == 2:
                print('Файл принят в обработку')
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                src = '/home/tele/money/content/' + message.document.file_name;
                with open(src, 'wb') as new_file:
                    new_file.write(downloaded_file)
                with open(src, 'rb') as f:
                    print(message.document.file_name)
                    dbx.files_upload(f.read(), '/' + message.document.file_name)
                with open('/home/tele/money/content/file', 'w') as f:
                    f.write(message.document.file_name)
                text = ''
                with open('/home/tele/money/content/text', 'r') as f:
                    text = f.read()
                print(dbx.files_get_temporary_link('/' + open('/home/tele/money/content/file', 'r').read()).link)
                send('<a href="' + dbx.files_get_temporary_link('/' + open('/home/tele/money/content/file', 'r').read()).link + '">&#8203;</a> %s' % text, key_send_admin(), message.chat.id)

@bot.message_handler(content_types=['video'])
def handle_docs_photo(message):
    with conn.cursor() as cur:
        cur.execute('SELECT mod FROM admins WHERE id = %s', (message.chat.id,))
        if bool(cur.rowcount):
            mod = cur.fetchone()[0]
            if mod == 2:
                print('Видео принято в обработку')
                file_info = bot.get_file(message.video.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                src = '/home/tele/money/content/video.mp4';# + message.video.file_id;
                with open(src, 'wb') as new_file:
                    new_file.write(downloaded_file)
                with open(src, 'rb') as f:
                    dbx.files_upload(f.read(), '/video.mp4')
                print(dbx.files_get_temporary_link('/video.mp4').link)
                send('<a href="' + dbx.files_get_temporary_link('/video.mp4').link + '">&#8203;</a> %s' % open('/home/tele/money/content/text', 'r').read(), key_send_video_admin(), message.chat.id)
# file_info = bot.get_file(message.document.file_id)
# downloaded_file = bot.download_file(file_info.file_path)
# src = '/home/tele/money/content/' + message.document.file_name;
# with open(src, 'wb') as new_file:
#     new_file.write(downloaded_file)

# bot.send_media_group(chatid,
# [InputMediaPhoto(msg.message.photo.file_id),
# InputMediaVideo(msg.message.video.file_id)])

# bot.send_message(id, '<a href="IMG_URL">&#8203;</a>',
#                  parse_mode="HTML")

@bot.message_handler(commands = ['admin'])
def admin_panel(message):
    with conn.cursor() as cur:
        cur.execute('SELECT name, pswd FROM admins WHERE id = %s', (message.chat.id,))
        if bool(cur.rowcount):
            row = cur.fetchall()
            name = row[0][0]
            pswd = row[0][1]
            if(pswd == message.text[7:]):
                send('Здравствуйте, ' + str(name).replace('None', '') + '.\nВы вошли как администратор', key_admin(), message.chat.id)
            else:
                send('❗️❗️❗️Неверный пароль❗️❗️❗️', key_main(), message.chat.id)
        else:
            send('❗️❗️❗️У Вас не доступа к этому разделу. О попытке получения привелигированного доступа с вашего аккаунта, будет сообщено администратору', key_menu(), message.chat.id)

@bot.message_handler(commands = ['start'])  #При подключении к боту выкидывать MENU
def start(message):
    if message.text[7:] != '':
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM users WHERE id = %s', (message.chat.id,))
            if not bool(cur.rowcount):
                cur.execute('SELECT id FROM users WHERE ref = %s', (message.text[7:],))
                if bool(cur.rowcount):
                    id_me = cur.fetchone()[0]
                    cur.execute('UPDATE users SET balance = balance + 200 WHERE id = %s', (id_me,))
                    cur.execute('INSERT INTO partners (id_me, id_partners) VALUES (%s, %s)', (id_me, message.chat.id))
                    conn.commit()
                    cur.execute('SELECT balance FROM users WHERE id = %s', (id_me,))
                    send("✅ Партнёр перешёл по вашей ссылке\n\n\
<b>Ваш баланс пополнен на 200 руб.</b>\n\n\
Баланс: <b> %s руб.</b>" % (cur.fetchone()[0]), key_main(), id_me)
                else:
                    print('Реф ссылка не найдена')
            else:
                print('Партнёр уже приглашен')

    with conn.cursor() as cur:
        id = message.chat.id
        cur.execute('SELECT id FROM users WHERE id = %s', (id,))
        if not bool(cur.rowcount):
            msg = bot.send_message(id ,'Привет. Я бот для зарабатывания денег.', reply_markup = key_main())
            hash = hashlib.md5(str(id).encode())
            name = str(message.chat.last_name) + ' ' + str(message.chat.first_name)
            time = str(datetime.datetime.today().strftime('%H.%M.%S'))
            cur.execute('INSERT INTO users (id, name, ref, balance, time, msg) VALUES (%s, %s, %s, 0, %s, %s)', (id, name, str(hash.hexdigest()), time, msg.message_id))
            cur.execute('UPDATE users SET active = %s WHERE id = %s', (datetime.datetime.today().strftime('%Y-%m-%d'), id))
            conn.commit()
        else:
            send("Меню", key_main(), id)
            cur.execute('UPDATE users SET active = %s WHERE id = %s', (datetime.datetime.today().strftime('%Y-%m-%d'), id))
            conn.commit()

@bot.message_handler(content_types=['text'])
def handler(message):
    with conn.cursor() as cur:
        id = message.chat.id
        cur.execute('UPDATE users SET active = %s WHERE id = %s', (datetime.datetime.today().strftime('%Y-%m-%d'), id))
        conn.commit()
        if(message.text == '🤑 Заработать'):
            send("Выберите способ заработка", key_money(), id)
        if(message.text == '👥 Партнеры'):
            send('Приглашайте партнёров в бот и \
получайте за них деньги!\n\
Отправьте другу ссылку в телеграме: \n\
' + partners(id, 1) + '\n\
200 руб. за каждого приглашенного Вами партнера\n\
Приглашённых пользователей: ' + partners(id, 2), key_main(), id)
        if(message.text == '❔ Помощь'):
            send("В этом боте очень простая система: ♻️каналы спонсоров платят боту за рекламу, а бот платит тебе за подписки на эти каналы!\
Выводить деньги из бота можно на: Сбербанк, Qiwi, ЯДеньги, WebMoney и др.\n\
📣Свой отзыв пиши мне: @xyu_pizda", key_main(), id)
        if(message.text == '💰 Баланс'):
            cur.execute('SELECT balance FROM users WHERE id = %s', (id,))
            send("Ваш баланс: <i>" + str(cur.fetchone()[0]) + " руб</i>\n\
<i>Минимальная сумма вывода: 3000 руб.</i>", key_main(), id)
        else:
            cur.execute('SELECT mod FROM admins WHERE id = %s', (id,))
            if bool(cur.rowcount):
                mod = cur.fetchone()[0]
                if mod == 1:
                    mailing_text(id, message.text)
                if mod == 2 and message.text == '!':
                    with open('/home/tele/money/content/text', 'r') as f:
                        send(f.read(), key, id)

@bot.callback_query_handler(func = lambda call: True) #Приём CALL_BACK_DATA с кнопок
def callback_inline(call):
    id = call.message.chat.id

    if call.data == 'send_video_post':
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM users')
            for r in cur.fetchall():
                print(r[0])
                try:
                    send('<a href="' + dbx.files_get_temporary_link('/video.mp4').link + '">&#8203;</a> %s' % open('/home/tele/money/content/text', 'r').read(), None, r[0])
                except:
                    print('Не удалось отправить сообщение')

    if call.data == 'send_post':
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM users')
            for r in cur.fetchall():
                print(r[0])
                try:
                    send('<a href="' + dbx.files_get_temporary_link('/' + open('/home/tele/money/content/file', 'r').read()).link + '">&#8203;</a> %s' % open('/home/tele/money/content/text', 'r').read(), None, r[0])
                except:
                    send(open('/home/tele/money/content/text', 'r').read(), None, r[0])
    if call.data == 'wefkbamklcsdfdsfhbffwca':
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM admins WHERE id = %s', (id,))
            if bool(cur.rowcount):
                mailing(id)

    if call.data == 'statistic_qsxcdlewgfwefwfafmag':
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM admins WHERE id = %s', (id,))
            if bool(cur.rowcount):
                name = cur.fetchone()[0]
                cur.execute('SELECT COUNT(id) FROM users')
                all = cur.fetchone()[0]
                cur.execute('SELECT COUNT(id) FROM users WHERE active - %s <= 7', (datetime.datetime.today().strftime('%Y-%m-%d'),))
                active = cur.fetchone()[0]
                cur.execute('SELECT COUNT(id_partners) FROM partners')
                ref = cur.fetchone()[0]
                send('Всего пользователей: ' + str(all) + '\n\
Активных(за неделю): ' + str(active) + '\nПриглашенных: ' + str(ref) + '\nРекламные ссылки: 0', key_exit_admin(), id)

    if call.data == 'ok_admin':
        with conn.cursor() as cur:
            cur.execute('SELECT name FROM admins WHERE id = %s', (id,))
            if bool(cur.rowcount):
                name = cur.fetchone()[0]
                send('Здравствуйте, ' + name.replace('None', '') + '.\nВы вошли как администратор', key_admin(), id)
                cur.execute('UPDATE admins SET mod = 0')
                conn.commit()

    if call.data == 'ok':
        send("Меню", key_main(), id)

    if call.data == 'say':
        send('Приглашайте партнёров в бот и \
получайте за них деньги!\n\
Отправьте другу ссылку в телеграме: \n\n\
' + partners(id, 1) + '\n\n\
200 руб. за каждого приглашенного Вами партнера\n\
Приглашённых пользователей: ' + partners(id, 2), key_main(), id)

    if call.data == 'follow':
        send('❌ Вы подписались уже на все каналы!', key_money(), id)

    if call.data == 'see':
        with conn.cursor() as cur:
            cur.execute('UPDATE users SET active = %s WHERE id = %s', (datetime.datetime.today().strftime('%Y-%m-%d'), id))
            conn.commit()
            cur.execute('SELECT time FROM users WHERE id = %s', (id,))
            now = datetime.datetime.today()
            then = datetime.datetime.strptime(str(cur.fetchone()[0]), '%H.%M.%S')
            delta = now - then
            if(delta.seconds < 3600):
                total = 3600 - delta.seconds
                minutes = (total % 3600) // 60
                seconds = total - (minutes * 60)
                send('Просмотр записей будет доступен через ' + str(minutes) + ' мин. ' + str(seconds) + ' сек.', key_money(), id)
            else:
                cur.execute('UPDATE users SET time = %s WHERE id = %s', (now.strftime('%H.%M.%S'), id))
                conn.commit()
                msg = send('Выполнено: 1 из 24', None, id)
                for i in range(25):
                    bot.edit_message_text(text = 'Выполено: ' + str(i) + ' из 25\n', chat_id = id, message_id = msg)
                send('Выполено: 25 из 25\n<b>Начислено: 50 руб.</b>', key_exit(), id)
                cur.execute('UPDATE users SET balance = balance + 50 WHERE id = %s', (id,))
                conn.commit()

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
