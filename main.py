import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ContentTypes
from datetime import datetime

import config as cfg
import markups as nav
from db import Database
from pyqiwip2p import QiwiP2P

# Конфигурация логов
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(levelname)s at %(asctime)s: %(message)s')

# Основной лог
file_handler_main = logging.FileHandler('main.log')
file_handler_main.setLevel(logging.INFO)
file_handler_main.setFormatter(formatter)
logger.addHandler(file_handler_main)

# Лог ошибок
file_handler_error = logging.FileHandler('err.log')
file_handler_error.setLevel(logging.WARNING)
file_handler_error.setFormatter(formatter)
logger.addHandler(file_handler_error)

logging.basicConfig(level=logging.INFO)

db = Database('db.db')


# Конфигурация телеграм-бота и оплаты на киви
bot = Bot(token=cfg.BOT_TOKEN)
dp = Dispatcher(bot)
p2p = QiwiP2P(auth_key=cfg.QIWI_TOKEN)

# Проверка, является ли строка числом
def is_number(_str):
    try:
        int(_str)
        return True
    except ValueError:
        return False

# Проверка, заблокирован ли пользователь
async def is_banned(user_id):
    if db.user_exists(user_id):
        if db.user_banned(user_id):
            logger.warning(f'Banned user {user_id} tried to access bot')
            return True
    else:
        logger.error(f'User {user_id} with no account tried to access bot')
        await bot.send_message(
            user_id,
            'Вам нужно создать аккаунт. Для этого используйте команду /start'
        )
        return True
    return False
# Обработка команды /start (инициализация пользователя)
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    if db.user_banned(user_id):
        logger.warning(f'Banned user {user_id} tried to access bot')
        banned = True
    else:
        banned = False
    if message.chat.type == 'private' and not banned:
        if not db.user_exists(user_id):
            db.add_user(user_id, message.from_user.username)

            logger.info(f'New user created with user_id: {user_id}.')
        await bot.send_message(
            user_id,
            (
            f'Привет, {message.from_user.username} \n\n' + \
            'Я - бот для пополнения баланса. \n' + \
            'Нажмите на кнопку, чтобы пополнить баланс. \n' + \
            'Снизу инлайн кнопка с текстом "Пополнить баланс"'
            ),
            reply_markup=nav.topUpMenu
        )

# Обработка команды /admin (админ панели)
@dp.message_handler(commands=['admin'])
async def start(message: types.Message):
    user_id = message.from_user.id
    if message.chat.type == 'private' and not await is_banned(user_id):
        await bot.send_message(
            user_id,
            'Админ панель',
            reply_markup=nav.adminMenu
        )

        logger.info(f'Admin panel accessed by user: {message.from_user.id}.')

# Обработки команды на изменение баланса пользователя /update <user_id> <balance>
@dp.message_handler(commands=['update'])
async def update(message: types.Message):
    user_id = message.from_user.id

    arguments = message.get_args().split(' ')
    if not await is_banned(user_id):
        try:
            db.set_money(arguments[0], arguments[1])
            await bot.send_message(user_id, f'Баланс успешно обновлен. Новый баланс пользователя {arguments[0]}: {arguments[1]} рублей')

            logger.info(f'User {user_id} manually set user {arguments[0]} balance to {arguments[1]} rubles.')
        except:
            await bot.send_message(user_id, "Ошибка. Неправильно введены параметры")

# Обработки команды на блокировку пользователя /ban <user_id>
@dp.message_handler(commands=['ban'])
async def ban(message: types.Message):
    user_id = message.from_user.id
    if not await is_banned(user_id):
        arguments = message.get_args().split(' ')
        try:
            db.ban(arguments[0])
            await bot.send_message(user_id, f'Пользователь успешно заблокирован')

            logger.info(f'User {arguments[0]} banned by user {user_id}.')
        except:
            await bot.send_message(user_id, "Ошибка. Неправильно введены параметры")

# Обработки команды на блокировку пользователя /unban <user_id>. В целях удобства дебага заблокированый пользователь может себя разблокировать
@dp.message_handler(commands=['unban'])
async def unban(message: types.Message):
    user_id = message.from_user.id
    arguments = message.get_args().split(' ')
    try:
        db.ban(arguments[0], state=0)
        await bot.send_message(user_id, f'Пользователь успешно разблокирован')

        logger.info(f'User {arguments[0]} unbanned by user {user_id}.')
    except:
        await bot.send_message(user_id, "Ошибка. Неправильно введены параметры")

# Обработка процесса создания счета на оплату. Для создания счета пользователь вводит число в чат. Это число - сумма счета.
@dp.message_handler()
async def bot_message(message: types.Message):
    user_id = message.from_user.id
    if message.chat.type == 'private' and not await is_banned(user_id):
        if is_number(message.text):
            message_money = int(message.text)
            bill = p2p.bill(amount=message_money, lifetime=5)

            db.add_check(user_id, message_money, bill.bill_id)
            await bot.send_message(
                user_id,
                f'Счет для оплаты {message_money} рублей: \n {bill.pay_url}.',
                reply_markup=nav.buy_menu(url=bill.pay_url, bill=bill.bill_id)
            )

            logger.info(f'User {user_id} created bill {bill.bill_id}. Amount: {message.text} rubles.')
        else:
            await bot.send_message(user_id, 'Введите целое число')

# Вывод информации по нажатию кнопки "пополнить счет"
@dp.callback_query_handler(text="top_up")
async def top_up(callback: types.CallbackQuery):
    await bot.delete_message(callback.from_user.id, callback.message.message_id)
    await bot.send_message(callback.from_user.id, 'Сумма пополнения:')

# Вывод информации по нажатию кнопки "изменить баланс пользователя"
@dp.callback_query_handler(text="update_balance")
async def update_balance(callback: types.CallbackQuery):
    await bot.delete_message(callback.from_user.id, callback.message.message_id)
    await bot.send_message(callback.from_user.id, 'Для изменения баланса: /update <id> <баланс>')

# Вывод информации по нажатию кнопки "заблокировать пользователя"
@dp.callback_query_handler(text="ban")
async def update_balance(callback: types.CallbackQuery):
    await bot.delete_message(callback.from_user.id, callback.message.message_id)
    await bot.send_message(callback.from_user.id, 'Для блокировки пользователя: /ban <id>')

# Выгрузка логов
@dp.callback_query_handler(text="send_logs")
async def send_logs(callback: types.CallbackQuery):
    logger.info(f'User {callback.from_user.id} accessed logs.')
    await bot.send_message(callback.from_user.id, 'Данные основных логов:')
    await bot.send_document(callback.from_user.id, open('main.log', 'rb'))
    await bot.send_message(callback.from_user.id, 'Данные логов ошибок и предупреждений:')
    await bot.send_document(callback.from_user.id, open('err.log', 'rb'))

# Выгрузка балансов пользователей
@dp.callback_query_handler(text="user_balances")
async def user_balances(callback: types.CallbackQuery):
    db_data = db.user_balances()
    balances = [f'Пользователь: {data[0]}, баланс: {data[1]} рублей' for data in db_data]
    await bot.send_message(callback.from_user.id, '\n'.join(balances))
    logger.info(f'User {callback.from_user.id} accessed user balances.')


# Обработка процесса оплаты созданного ранее счета
@dp.callback_query_handler(text_contains="check_")
async def check(callback: types.CallbackQuery):
    bill = str(callback.data[6:])
    info = db.get_check(bill)
    if info:
        if str(p2p.check(bill_id=bill).status) == 'PAID':
            user_money = db.user_money(callback.from_user.id)
            money = int(info[2])
            db.set_money(callback.from_user.id, user_money+money)
            await bot.send_message(callback.from_user.id, f'Счет пополнен. Баланс: {user_money+money}')

            logger.info(f'Bill {bill.bill_id} was paid successfully. Amount:  {message.text} rubles. Current balance for user {callback.from_user.id}: {user_money} rubles.')
        else:
            await bot.send_message(
                callback.from_user.id,
                'Счет не оплачен',
                reply_markup=nav.buy_menu(False, bill=bill),
            )
    else:
        await bot.send_message(callback.from_user.id, 'Счет не найден')

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
