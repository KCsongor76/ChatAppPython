import datetime
import socket
import threading

from Message import Message
import mysql.connector
from actionConsts import *

db_config = {
    'host': "localhost",
    'user': "root",
    'password': "",
    'database': "chat_app_db",
}


class ServerClass:
    def __init__(self, host, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.clients = {}  # To store client connections

    def start(self):
        print("Server started. Waiting for connections...")
        while True:
            client_socket, client_address = self.server.accept()
            print(f"Connection from {client_address} established.")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client):
        while True:
            try:
                message = client.recv(1024).decode("utf-8")
                if message:
                    # Process messages from client
                    self.process_message2(client, message)
            except ConnectionResetError:
                print("Connection closed by client.")
                break

    # def process_message(self, client, message):
    #     # message = login, username, password
    #     # message = message, message
    #     msg_parts = message.split(",")
    #     action = msg_parts[0]
    #     if action == "login":
    #         username = msg_parts[1]
    #         password = msg_parts[2]
    #         if self.validate_user(username, password):
    #             client.send("Login successful".encode("utf-8"))
    #             self.clients[client] = username
    #             # TODO: start here
    #             all_messages = self.fetch_general_messages()
    #             for message in all_messages:
    #                 self.self_broadcast(f"{message[0]}: {message[1]}\n", client)
    #             # TODO: ends here
    #             self.broadcast(f"{username} has joined the chat.")
    #         else:
    #             client.send("Invalid username or password".encode("utf-8"))
    #     elif action == "message":
    #         # TODO:
    #         self.insert_general_message(self.clients[client], msg_parts[1])
    #         self.broadcast(f"{self.clients[client]}: {msg_parts[1]}")
    #     else:
    #         pass

    def process_message2(self, client, message):
        msg = Message.from_json(message)
        if msg.action == LOGIN:
            username = msg.username
            password = msg.password
            if self.validate_user(username, password):
                if username in self.clients.values():
                    m = Message(action=UNSUCCESSFUL_LOGIN, message="Already logged in!")
                    client.send(m.to_json().encode("utf-8"))
                else:
                    self.clients[client] = username
                    all_messages = self.fetch_general_messages()
                    msg_to_client = Message(action=SUCCESSFUL_LOGIN, message=all_messages, username=username)
                    client.send(msg_to_client.to_json().encode("utf-8"))
                    self.broadcast(action=BROADCAST, message_string=f"{username} has joined the chat.")
            else:
                m = Message(action=UNSUCCESSFUL_LOGIN, message="Invalid username or password")
                client.send(m.to_json().encode("utf-8"))
        elif msg.action == GENERAL_MESSAGE:
            if msg.message == "" or msg.message is None:
                pass
            else:
                sender = self.clients[client]
                self.insert_general_message(sender, msg.message)
                self.broadcast(action=BROADCAST, message_string=f"{sender}: {msg.message}")
        elif msg.action == GET_USERNAMES:
            usernames = self.fetch_usernames_from_db(self.clients[client])
            message = Message(action=USER_LIST, message=usernames)
            client.send(message.to_json().encode("utf-8"))
        elif msg.action == GET_PRIVATE_MESSAGES:
            private_messages = self.fetch_private_messages(sender=self.clients[client], receiver=msg.username)
            print(f"private_messages: {private_messages}")
            message = Message(action=SHOW_PRIVATE_MESSAGES, message=private_messages)
            client.send(message.to_json().encode("utf-8"))
            print("sent")
        elif msg.action == PRIVATE_MESSAGE:
            if msg.message == "" or msg.message is None:
                pass
            else:
                sender = self.clients[client]
                receiver = msg.username
                message = msg.message
                self.insert_private_message(sender, receiver, message)
                msg = Message(action=PRIVATE_BROADCAST, message=f"{sender}: {message}", username=receiver)
                client.send(msg.to_json().encode("utf-8"))
                for cli in self.clients:
                    if self.clients[cli] == receiver:
                        cli.send(msg.to_json().encode("utf-8"))

    def broadcast(self, action, message_string):
        for client in self.clients:
            try:
                message = Message(action=action, message=message_string, username=self.clients[client])
                client.send(message.to_json().encode("utf-8"))
            except ConnectionResetError:
                self.remove_client(client)

    def self_broadcast(self, message_string, self_client):
        message = Message(action=BROADCAST, message=message_string, username=self_client)
        try:
            self_client.send(message.to_json().encode("utf-8"))
        except ConnectionResetError:
            self.remove_client(self_client)

    def remove_client(self, client):
        if client in self.clients:
            username = self.clients[client]
            del self.clients[client]
            self.broadcast(action=BROADCAST, message_string=f"{username} has left the chat.")
            client.close()

    def validate_user(self, username, password):
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()

        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        cursor.close()
        db.close()
        return user is not None

    def fetch_usernames_from_db(self, self_username):
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()

        query = "SELECT username FROM users WHERE username <> %s"
        cursor.execute(query, (self_username,))
        usernames = [row[0] for row in cursor.fetchall()]

        cursor.close()
        db.close()

        return usernames

    def insert_general_message(self, sender, message):
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()

        query = "INSERT INTO general_messages (sender, message, timestamp) VALUES (%s, %s, %s)"
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(query, (sender, message, timestamp))

        db.commit()
        cursor.close()
        db.close()

    def insert_private_message(self, sender, receiver, message):
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()

        query = "INSERT INTO private_messages (sender, receiver, message, timestamp) VALUES (%s, %s, %s, %s)"
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(query, (sender, receiver, message, timestamp))

        db.commit()
        cursor.close()
        db.close()

    def fetch_general_messages(self):
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()

        query = "SELECT sender, message FROM general_messages"
        cursor.execute(query)
        all_messages = cursor.fetchall()

        cursor.close()
        db.close()

        return all_messages

    def fetch_private_messages(self, sender, receiver):
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()

        query = \
            (""
             "SELECT sender, message "
             "FROM private_messages "
             "WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s)"
             )
        cursor.execute(query, (sender, receiver, receiver, sender))
        # all_messages = [row[0] for row in cursor.fetchall()]
        all_messages = cursor.fetchall()

        cursor.close()
        db.close()

        return all_messages


if __name__ == "__main__":
    HOST = '192.168.1.4'
    PORT = 5555
    server = ServerClass(HOST, PORT)
    server.start()
