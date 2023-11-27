import socket
import threading

from Message import Message
from actionConsts import *
from DatabaseFunctions import *


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

    def broadcast(self, action, message_string):
        """
        Sending message to every client available, depending on the action
        (action -> what kind of Message object is sent)
        :param action:
        :param message_string:
        :return:
        """
        for client in self.clients:
            try:
                message = Message(action=action, message=message_string, username=self.clients[client])
                client.send(message.to_json().encode("utf-8"))
            except ConnectionResetError:
                self.remove_client(client)

    def self_broadcast(self, message_string, self_client):
        """
        Sending a broadcasting message only to the selected client
        :param message_string:
        :param self_client:
        :return:
        """
        message = Message(action=BROADCAST, message=message_string, username=self_client)
        try:
            self_client.send(message.to_json().encode("utf-8"))
        except ConnectionResetError:
            self.remove_client(self_client)

    def remove_client(self, client):
        """
        Remove client from the app, and broadcast a message.
        :param client:
        :return:
        """
        if client in self.clients:
            username = self.clients[client]
            del self.clients[client]
            self.broadcast(action=BROADCAST, message_string=f"{username} has left the chat.")
            client.close()

    def handle_client(self, client):
        """
        Handling incoming messages/requests from the clients.
        :param client:
        :return:
        """
        while True:
            try:
                message = client.recv(1024).decode("utf-8")
                if message:
                    # Process messages from client
                    self.process_message(client, message)
            except ConnectionResetError:
                print("Connection closed by client.")
                break

    def process_message(self, client, message):
        """
        Processing message/request from client
        :param client:
        :param message:
        :return:
        """
        msg = Message.from_json(message)
        if msg.action == LOGIN:
            self.handle_login_action(msg, client)
        elif msg.action == GENERAL_MESSAGE:
            self.handle_general_message_action(msg, client)
        elif msg.action == GET_USERNAMES:
            self.handle_get_usernames_action(client)
        elif msg.action == GET_PRIVATE_MESSAGES:
            self.handle_get_private_messages_action(msg, client)
        elif msg.action == PRIVATE_MESSAGE:
            self.handle_private_message_action(msg, client)

    def handle_login_action(self, msg, client):
        """
        Checking if username-password pair exists in the database, if yes,
         it checks if that user is already logged in or not. If everything checks out,
         fetches all the previous general messages, and
        :param msg:
        :param client:
        :return:
        """
        username = msg.username
        password = msg.password
        if validate_user(username, password):
            if username in self.clients.values():
                m = Message(action=UNSUCCESSFUL_LOGIN, message="Already logged in!")
                client.send(m.to_json().encode("utf-8"))
            else:
                self.clients[client] = username
                all_messages = fetch_general_messages()
                msg_to_client = Message(action=SUCCESSFUL_LOGIN, message=all_messages, username=username)
                client.send(msg_to_client.to_json().encode("utf-8"))
                self.broadcast(action=BROADCAST, message_string=f"{username} has joined the chat.")
        else:
            m = Message(action=UNSUCCESSFUL_LOGIN, message="Invalid username or password")
            client.send(m.to_json().encode("utf-8"))

    def handle_general_message_action(self, msg, client):
        """
        General chat: inserts the received message to the database, and
        broadcasts it for the clients
        :param msg:
        :param client:
        :return:
        """
        if msg.message == "" or msg.message is None:
            pass
        else:
            sender = self.clients[client]
            insert_general_message(sender, msg.message)
            self.broadcast(action=BROADCAST, message_string=f"{sender}: {msg.message}")

    def handle_get_usernames_action(self, client):
        """
        General chat: shows the available users namelist, so we can send private messages.
        :param client:
        :return:
        """
        usernames = fetch_usernames_from_db(self.clients[client])
        message = Message(action=USER_LIST, message=usernames)
        client.send(message.to_json().encode("utf-8"))

    def handle_get_private_messages_action(self, msg, client):
        """
        Private chat: shows previous chats
        :param msg:
        :param client:
        :return:
        """
        private_messages = fetch_private_messages(sender=self.clients[client], receiver=msg.username)
        message = Message(action=SHOW_PRIVATE_MESSAGES, message=private_messages)
        client.send(message.to_json().encode("utf-8"))

    def handle_private_message_action(self, msg, client):
        """
        Receives and inserts new private message to the database
        :param msg:
        :param client:
        :return:
        """
        if msg.message == "" or msg.message is None:
            pass
        else:
            sender = self.clients[client]
            receiver = msg.username
            message = msg.message
            insert_private_message(sender, receiver, message)
            msg = Message(action=PRIVATE_BROADCAST, message=f"{sender}: {message}", username=receiver)
            client.send(msg.to_json().encode("utf-8"))
            for cli in self.clients:
                if self.clients[cli] == receiver:
                    cli.send(msg.to_json().encode("utf-8"))


if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 5555
    server = ServerClass(HOST, PORT)
    server.start()
