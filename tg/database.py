import psycopg2


class DataBase:

    def __init__(self):
        # подключение к базе данных
        self.connection = psycopg2.connect(database='pdb',
                                           user='postgres',
                                           password='posTforRusskih_113',
                                           host='localhost',
                                           port='5432')
        self.cursor = self.connection.cursor()

    # регистрация зрителя
    def add_viewer(self, data):
        with self.connection:
            query = "INSERT INTO viewer (user_id, number) values (%s, %s)"
            self.cursor.executemany(query, [data])
            self.connection.commit()

    # проверка зарегистрирован ли зритель в базе
    def check_viewer(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT *FROM viewer WHERE user_id = {user_id}")
            self.connection.commit()
            return self.cursor.fetchall()

    def check_which_events_is_user_on(self, user_id):
        with self.connection:
            self.cursor.execute("SELECT events.name, viewer.number FROM viewer, events WHERE viewer.number"
                                f" BETWEEN events.tickets_from AND events.tickets_to AND viewer.user_id = {user_id}")
            self.connection.commit()
            return self.cursor.fetchall()

    # удаление зрителя из базы
    def remove_viewer(self, user_id):
        with self.connection:
            self.cursor.execute("DELETE FROM viewer WHERE user_id = %s" % user_id)
            self.connection.commit()

    # проверка зарегистрирован ли журналист в базе
    def check_journalist(self, user_id):
        with self.connection:
            self.cursor.execute("SELECT *FROM journalist WHERE user_id = %s" % user_id)
            self.connection.commit()
            return bool(self.cursor.fetchall())

    # регистрация журналиста
    def add_journalist(self, data):
        if DataBase.check_journalist(self, data[0]):  # data[0] =id
            DataBase.remove_journalist(self, data[0])
        with self.connection:
            query = "INSERT INTO journalist (user_id, number, redaction) values (%s, %s, %s)"
            self.cursor.executemany(query, [data])
            self.connection.commit()

    # удаление журналиста из базы
    def remove_journalist(self, user_id):
        with self.connection:
            self.cursor.execute("DELETE FROM journalist WHERE user_id = %s" % user_id)
            self.connection.commit()

    # провека прав администратора
    def check_admin(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT *FROM journalist WHERE user_id = {user_id}")
            self.connection.commit()
            return bool(self.cursor.fetchall())

    # добавление мероприятия
    def add_event(self, data):
        with self.connection:
            query = f"INSERT INTO events (name, tickets_from, tickets_to) values {data[0], data[1], data[2]}"
            self.cursor.execute(query)
            self.connection.commit()

