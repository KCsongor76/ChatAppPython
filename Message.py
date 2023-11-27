import json


class Message:
    def __init__(self, action, message=None, username=None, password=None):
        self.action = action
        self.message = message
        self.username = username
        self.password = password

    def to_json(self):
        return json.dumps({
            'action': self.action,
            'message': self.message,
            'username': self.username,
            'password': self.password,
        })

    @classmethod
    def from_json(cls, json_string):
        data = json.loads(json_string)
        return cls(
            action=data['action'],
            message=data['message'],
            username=data['username'],
            password=data['password'],
        )
