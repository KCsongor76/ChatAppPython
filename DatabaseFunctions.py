import datetime
import mysql.connector

db_config = {
    'host': "localhost",
    'user': "root",
    'password': "",
    'database': "chat_app_db",
}


def connect_to_db():
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    return db, cursor


def close_connection(db, cursor):
    cursor.close()
    db.close()


def validate_user(username, password):
    db, cursor = connect_to_db()

    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    user = cursor.fetchone()

    close_connection(db, cursor)
    return user is not None


def fetch_usernames_from_db(self_username):
    db, cursor = connect_to_db()

    query = "SELECT username FROM users WHERE username <> %s"
    cursor.execute(query, (self_username,))
    usernames = [row[0] for row in cursor.fetchall()]

    close_connection(db, cursor)

    return usernames


def insert_general_message(sender, message):
    db, cursor = connect_to_db()

    query = "INSERT INTO general_messages (sender, message, timestamp) VALUES (%s, %s, %s)"
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(query, (sender, message, timestamp))

    db.commit()
    close_connection(db, cursor)


def insert_private_message(sender, receiver, message):
    db, cursor = connect_to_db()

    query = "INSERT INTO private_messages (sender, receiver, message, timestamp) VALUES (%s, %s, %s, %s)"
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(query, (sender, receiver, message, timestamp))

    db.commit()
    close_connection(db, cursor)


def fetch_general_messages():
    db, cursor = connect_to_db()

    query = "SELECT sender, message FROM general_messages"
    cursor.execute(query)
    all_messages = cursor.fetchall()

    close_connection(db, cursor)

    return all_messages


def fetch_private_messages(sender, receiver):
    db, cursor = connect_to_db()

    query = \
        (""
         "SELECT sender, message "
         "FROM private_messages "
         "WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s)"
         )
    cursor.execute(query, (sender, receiver, receiver, sender))
    # all_messages = [row[0] for row in cursor.fetchall()]
    all_messages = cursor.fetchall()

    close_connection(db, cursor)

    return all_messages
