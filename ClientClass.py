import tkinter as tk
import socket
import threading

from Message import Message
from actionConsts import *


class ClientClass:
    def __init__(self, host, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))

        self.root = tk.Tk()
        self.login_page()
        self.root.mainloop()

        self.title_username = None

    def login_page(self):
        self.root.title("Chat App - Login")

        self.username_label = tk.Label(self.root, text="Username:")
        self.password_label = tk.Label(self.root, text="Password:")

        self.username_entry = tk.Entry(self.root)
        self.password_entry = tk.Entry(self.root, show="*")

        self.username_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)

        self.password_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.password_entry.grid(row=1, column=1, padx=10, pady=5)

        self.error_label = tk.Label(self.root, text="", fg="red")
        self.login_button = tk.Button(self.root, text="Login", command=self.login)

        self.error_label.grid(row=2, columnspan=2, pady=5)
        self.login_button.grid(row=3, columnspan=2, pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        login_msg = Message(action=LOGIN, username=username, password=password)
        self.client.send(login_msg.to_json().encode("utf-8"))
        response = self.client.recv(1024).decode("utf-8")
        msg = Message.from_json(response)
        if msg.action == SUCCESSFUL_LOGIN:
            self.load_chat_page()
            for message in msg.message:
                self.display_message(f"{message[0]}: {message[1]}")
        else:
            self.error_label.config(text=msg.message)

    def load_chat_page(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title("Chat App - Main Chat")

        self.user_list = tk.Listbox(self.root)
        self.user_list.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)

        # self.start_button = tk.Button(self.root, text="Start", command=self.show_private_messages)
        # self.start_button.pack()

        self.chat_display = tk.Text(self.root, state=tk.DISABLED)
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.message_entry = tk.Entry(self.root)
        self.message_entry.pack(fill=tk.BOTH, padx=5, pady=5)

        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.pack()

        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.start()

        # Request usernames from the server
        request_msg = Message(action=GET_USERNAMES)
        self.client.send(request_msg.to_json().encode("utf-8"))

        # Receive and process usernames from the server
        response = self.client.recv(1024).decode("utf-8")
        print(response)
        usernames_msg = Message.from_json(response)
        print(usernames_msg)
        if usernames_msg.action == USER_LIST:
            usernames = usernames_msg.message
            for username in usernames:
                self.user_list.insert(tk.END, username)
        # TODO:
        self.user_list.bind('<Double-Button-1>', self.show_private_messages)

    def show_private_messages(self, event):
        try:
            # print("show private_messages")
            selected_user = self.user_list.get(tk.ACTIVE)
            if selected_user:
                self.load_private_chat(selected_user)
                self.root.withdraw()

                message = Message(action=GET_PRIVATE_MESSAGES, username=selected_user)
                self.client.send(message.to_json().encode("utf-8"))
        except Exception as e:
            print(f"Error: {e}")

    def load_private_chat(self, selected_user):
        try:
            self.title_username = selected_user

            self.private_chat_window = tk.Toplevel(self.root)
            self.private_chat_window.title(f"Private Chat - {selected_user}")

            self.private_chat_display = tk.Text(self.private_chat_window, state=tk.DISABLED)
            self.private_chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            self.private_message_entry = tk.Entry(self.private_chat_window)
            self.private_message_entry.pack(fill=tk.BOTH, padx=5, pady=5)

            self.private_send_button = tk.Button(self.private_chat_window, text="Send",
                                                 command=lambda: self.send_private_message(selected_user))
            self.private_send_button.pack()

            self.go_back_button = tk.Button(self.private_chat_window, text="Go back", command=self.go_back)
            self.go_back_button.pack()

            self.private_receive_thread = threading.Thread(target=self.receive_messages, args=(selected_user,))
            self.private_receive_thread.start()

        except Exception as e:
            print(f"Error: {e}")

    def go_back(self):
        self.private_chat_window.destroy()
        self.root.deiconify()
        # self.load_chat_page()

    def send_private_message(self, selected_user):
        message = self.private_message_entry.get()
        send_msg = Message(action=PRIVATE_MESSAGE, message=message, username=selected_user)
        self.client.send(send_msg.to_json().encode("utf-8"))
        self.private_message_entry.delete(0, tk.END)

    # def receive_private_messages(self, selected_user):
    #     while True:
    #         try:
    #             message = self.client.recv(1024).decode("utf-8")
    #             msg = Message.from_json(message)
    #             msg.username = selected_user
    #             if msg.action == PRIVATE_BROADCAST:
    #                 self.display_private_message(msg.message)
    #         except ConnectionResetError:
    #             print("Disconnected from the server.")
    #             break

    def receive_messages(self):
        while True:
            try:
                response = self.client.recv(1024).decode("utf-8")
                message = Message.from_json(response)

                if message.action == BROADCAST:
                    self.display_message(message.message)
                elif message.action == PRIVATE_BROADCAST:
                    self.display_private_message(message.message)
                elif message.action == SHOW_PRIVATE_MESSAGES:
                    for msg in message.message:
                        self.display_private_message(f"{msg[0]}: {msg[1]}", message.username)
            except ConnectionResetError:
                print("Disconnected from the server.")
                break

    def display_private_message(self, message, receiver=None):
        print("display_private_message")
        if receiver == self.title_username or receiver is None:
            self.private_chat_display.config(state=tk.NORMAL)
            self.private_chat_display.insert(tk.END, message + "\n")
            self.private_chat_display.config(state=tk.DISABLED)
            self.private_chat_display.see(tk.END)

    def send_message(self):
        message_string = self.message_entry.get()
        message = Message(action=GENERAL_MESSAGE, message=message_string)
        self.client.send(message.to_json().encode("utf-8"))
        self.message_entry.delete(0, tk.END)

    def display_message(self, message):
        # print("display_message")
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)


if __name__ == "__main__":
    HOST = '192.168.1.4'
    PORT = 5555
    client = ClientClass(HOST, PORT)
