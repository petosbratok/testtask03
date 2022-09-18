from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

btnTopUp = InlineKeyboardButton(text='Пополнить баланс', callback_data="top_up")
topUpMenu = InlineKeyboardMarkup(row_width=1)
topUpMenu.insert(btnTopUp)

def buy_menu(isUrl=True, url='', bill=''):
    qiwiMenu = InlineKeyboardMarkup(row_width=1)

    if isUrl:
        btnUrlQiwi = InlineKeyboardButton(text="Ссылка на оплату", url=url)
        qiwiMenu.insert(btnUrlQiwi)

    btnCheckQiwi = InlineKeyboardButton(text="Проверить оплату", callback_data="check_"+bill)
    qiwiMenu.insert(btnCheckQiwi)
    return qiwiMenu

btnBalance = InlineKeyboardButton(text='Выгрузка логов', callback_data="send_logs")
btnLog = InlineKeyboardButton(text='Выгрузка балансов пользователей', callback_data="user_balances")
btnBalanceUpdate = InlineKeyboardButton(text='Изменить баланс пользователя', callback_data="update_balance")
btnBlockUser = InlineKeyboardButton(text='Заблокировать пользователя', callback_data="ban")
adminMenu = InlineKeyboardMarkup(row_width=1)
adminMenu.insert(btnBalance)
adminMenu.insert(btnLog)
adminMenu.insert(btnBalanceUpdate)
adminMenu.insert(btnBlockUser)
