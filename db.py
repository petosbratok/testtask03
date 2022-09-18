import sqlite3

class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    # Проверить, существует ли пользователь
    def user_exists(self, user_id):
        with self.connection:
            result = self.cursor.execute(f"SELECT * FROM users WHERE user_id = {user_id}").fetchall()
            return bool(len(result))

    # Проверить, забанен ли пользователь
    def user_banned(self, user_id):
        with self.connection:
            result = self.cursor.execute(f"SELECT * FROM users WHERE user_id = {user_id} and banned = 1").fetchall()
            return bool(len(result))

    # Создать пользователя
    def add_user(self, user_id, username):
        with self.connection:
            return self.cursor.execute(f"INSERT INTO users (user_id, username) VALUES ({user_id}, '{username}')")

    # Вернуть баланс пользователя
    def user_money(self, user_id):
        with self.connection:
            result = self.cursor.execute(f"SELECT money FROM users WHERE user_id = {user_id}").fetchmany(1)
            return int(result[0][0])

    # Получить балансы всех пользователей
    def user_balances(self):
        with self.connection:
            return self.cursor.execute(f"SELECT user_id, money FROM users").fetchmany(1)


    # Установить баланс определенного пользователя
    def set_money(self, user_id, money):
        with self.connection:
            return self.cursor.execute(f"UPDATE 'users' SET 'money' = {int(money)} WHERE user_id = {int(user_id)}")

    # Заблокировать пользователя
    def ban(self, user_id, state=1):
        with self.connection:
            return self.cursor.execute(f"UPDATE 'users' SET 'banned' = {state} WHERE user_id = {int(user_id)}")

    # Добавить счет на оплату в базу данных
    def add_check(self, user_id, money, bill_id):
        with self.connection:
            self.cursor.execute(f"INSERT INTO 'check' ('user_id', 'money', 'bill_id') VALUES ({user_id}, {money}, '{bill_id}')")

    # Получить информацию об определенном счете на оплату
    def get_check(self, bill_id):
        print(bill_id)
        with self.connection:
            result = self.cursor.execute(f"SELECT * FROM 'check' WHERE bill_id = '{bill_id}'").fetchmany(1)
            if result:
                return result[0]
            return False
