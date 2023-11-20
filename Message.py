import json


class Message:
    def __init__(self, action, message=None, username=None, password=None, receiver_client=None, sender_client=None):
        self.action = action
        self.message = message
        self.username = username
        self.password = password
        self.receiver_client = receiver_client
        self.sender_client = sender_client

        # TODO: implement overloading logic

    def to_json(self):
        return json.dumps({
            'action': self.action,
            'message': self.message,
            'username': self.username,
            'password': self.password,
            'sender_client': self.sender_client,
            'receiver_client': self.receiver_client
        })

    @classmethod
    def from_json(cls, json_string):
        data = json.loads(json_string)
        return cls(
            action=data['action'],
            message=data['message'],
            username=data['username'],
            password=data['password'],
            receiver_client=data['receiver_client'],
            sender_client=data['sender_client']
        )

# # Example Usage:
#
# # Create a Message object
# message = Message('SEND_MESSAGE_TO_ALL_CHAT', 'Hello, everyone!')
#
# # Convert Message object to JSON string
# json_message = message.to_json()
# print("JSON Message:", json_message)
#
# # Create a Message object from a JSON string
# received_message = Message.from_json(json_message)
# print("Received Message:")
# print("Action:", received_message.action)
# print("Message:", received_message.message)
# print("Sender Client:", received_message.sender_client)
# print("Receiver Client:", received_message.receiver_client)
